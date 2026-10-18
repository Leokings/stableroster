"""Operator-attested recovery for a proven pre-broadcast nonce-read failure.

This cannot prove the SDK failure stage by itself. Use only after reviewing the
exception trace and confirming no write was signed or sent. It retains the old
entry and readbacks in a reconciliation record, never silently deletes history.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from release_readonly import read_public, rpc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", required=True)
    parser.add_argument("--confirm-before-broadcast", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.confirm_before_broadcast:
        raise SystemExit("Operator must first verify the exception happened before signing/broadcast")
    root = Path(__file__).resolve().parents[1]
    path = root / ".studionet-runs" / "v2.json"
    if path.with_suffix(".lock").exists():
        raise SystemExit("Live process is active; do not reconcile concurrently")
    record = json.loads(path.read_text())
    entry = record["steps"][args.step]
    assert entry["status"] == "SUBMISSION_UNCERTAIN" and entry["transaction_hash"] is None
    call = entry["request"]
    assert call["method"] == "respond_pair" and call["expected_error"] is None
    sender = call["sender"]
    latest = int(rpc("eth_getTransactionCount", [sender, "latest"]), 16)
    pending = int(rpc("eth_getTransactionCount", [sender, "pending"]), 16)
    assert latest == pending == 0, "only an untouched fresh sender is supported"
    roster_id, side, index, accept = call["args"]
    state = read_public(call["address"], "get_roster", [roster_id], record["binding"]["wallet_addresses"][0])
    assert state["state"] == "AWAITING_RESPONSES"
    assert state["left" if side == "LEFT" else "right"][index]["wallet"].lower() == sender
    assert state["left_responses" if side == "LEFT" else "right_responses"][index] == "PENDING"
    event = {"step": args.step, "original_entry": entry, "latest_nonce": latest, "pending_nonce": pending,
             "operator_attestation": "Reviewed SDK trace: HTTP 502 at eth_getTransactionCount before signing/broadcast",
             "observed_final_state": state, "reconciled_at": datetime.now(timezone.utc).isoformat()}
    if args.apply:
        record.setdefault("reconciliations", []).append(event)
        del record["steps"][args.step]
        temporary = path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    print(json.dumps({"step": args.step, "sender": sender, "latest_nonce": latest,
                      "pending_nonce": pending, "state": state["state"], "applied": args.apply}))


if __name__ == "__main__":
    main()
