"""Opt-in StudioNet transactions with an ignored, resumable public journal.

SDK calls are the hash-returning deploy_contract/write_contract methods, followed
by wait_for_transaction_receipt. No private key is written to this journal.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus


class StudioJournal:
    def __init__(self, repository, source, accounts, *, client=None, path=None):
        if client is None:
            if os.environ.get("RUN_STUDIONET") != "1":
                raise RuntimeError("live_test_not_authorized")
            from tests.studionet_support import install_rpc_timeouts
            install_rpc_timeouts()
            from gltest.clients import get_gl_client
            client = get_gl_client()
        if client.chain.id != 61999 or client.provider.url.rstrip("/") != "https://studio.genlayer.com/api":
            raise RuntimeError("wrong_live_network")
        self.client = client
        self.source = Path(source)
        # gltest clears .artifacts on startup; checkpoints must live elsewhere.
        self.path = Path(path) if path else self.source.parents[1] / ".studionet-runs" / "v2.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.path.with_suffix(".lock")
        self.binding = {
            "repository": repository,
            "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "wallet_addresses": [str(account.address).lower() for account in accounts],
            "rpc": client.provider.url.rstrip("/"),
        }
        self.record = None

    def __enter__(self):
        try:
            self.lock = self.lock_path.open("x", encoding="utf-8")
        except FileExistsError:
            raise RuntimeError("journal_locked: reconcile any interrupted process before removing the lock") from None
        try:
            if self.path.exists():
                self.record = json.loads(self.path.read_text(encoding="utf-8"))
                if self.record["binding"] != self.binding:
                    raise RuntimeError("journal_binding_mismatch")
            else:
                self.record = {"schema": "studionet-v2-test-journal/v1", "binding": self.binding,
                               "status": "NOT_SUBMITTED", "parameters": {}, "steps": {}}
                self._save()
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        self.lock.close()
        self.lock_path.unlink()

    def _save(self):
        temporary = self.path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(self.record, sort_keys=True, indent=2))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)

    def parameter(self, key, create):
        if key not in self.record["parameters"]:
            self.record["parameters"][key] = create()
            self._save()
        return self.record["parameters"][key]

    def transaction(self, step, account, args, *, address=None, method=None, expected_error=None):
        request = {"address": address, "method": method, "args": args,
                   "sender": str(account.address).lower(), "expected_error": expected_error}
        entry = self.record["steps"].get(step)
        if entry is not None and entry["request"] != request:
            raise RuntimeError("journal_request_mismatch")
        if entry is None:
            entry = {"request": request, "status": "SUBMISSION_UNCERTAIN", "transaction_hash": None}
            self.record["steps"][step] = entry
            self.record["status"] = "IN_PROGRESS"
            self._save()
            # If the process dies between broadcast and this checkpoint, do not
            # auto-resubmit. Reconcile the nonce and public transaction manually.
            if method is None:
                tx_hash = self.client.deploy_contract(code=self.source.read_bytes(), args=args, account=account)
            else:
                tx_hash = self.client.write_contract(address=address, function_name=method, args=args, account=account)
            entry.update(transaction_hash=str(tx_hash), status="SUBMITTED")
            self._save()  # Persist the hash BEFORE waiting for finality.
        if entry["transaction_hash"] is None:
            raise RuntimeError("submission_uncertain: reconcile the prior broadcast; no automatic resubmission")
        print(f"STUDIONET step={step} status={entry['status']} transaction={entry['transaction_hash']}", flush=True)
        if "receipt" not in entry:
            try:
                receipt = self.client.wait_for_transaction_receipt(
                    transaction_hash=entry["transaction_hash"], status=TransactionStatus.FINALIZED,
                    interval=6000, retries=100)
            except Exception:
                entry["status"] = "PENDING"
                self._save()
                raise
            if receipt.get("status_name") != TransactionStatus.FINALIZED.value:
                raise AssertionError("receipt_not_finalized")
            success = tx_execution_succeeded(receipt)
            entry.update(status="FINALIZED_SUCCESS" if success else "FINALIZED_ERROR",
                         execution_success=success, receipt=receipt)
            self._save()
        receipt = entry["receipt"]
        success = tx_execution_succeeded(receipt)
        if expected_error is None:
            assert success, "finalized_execution_failed"
        else:
            assert not success and expected_error in json.dumps(receipt), "expected_rejection_not_proven"
        return receipt

    def readback(self, step, observed):
        entry = self.record["steps"][step]
        assert entry["status"] in ("FINALIZED_SUCCESS", "FINALIZED_ERROR")
        if "final_state_readback" not in entry:
            entry["final_state_readback"] = observed
        elif entry["final_state_readback"] != observed:
            # Never rewrite the original post-step observation when resuming
            # after later transactions have legitimately changed public state.
            resumed = entry.setdefault("resumed_readbacks", [])
            if not resumed or resumed[-1] != observed:
                assert len(resumed) < 8, "too_many_resumed_readbacks"
                resumed.append(observed)
        self._save()

    def finish(self, source_proof, observed):
        assert source_proof["source_sha256"] == self.binding["source_sha256"]
        assert source_proof["deployed_source_sha256"] == self.binding["source_sha256"]
        assert all(step["status"] in ("FINALIZED_SUCCESS", "FINALIZED_ERROR")
                   for step in self.record["steps"].values())
        self.record.update(status="VERIFIED", source=source_proof, observed=observed)
        self._save()
