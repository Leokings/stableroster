"""Shared helpers for opt-in StudioNet verification.

Wallet bundles contain secrets and must remain outside this repository.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any
from urllib import error, request

from genlayer_py import create_account
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus


STUDIONET_RPC = "https://studio.genlayer.com/api"


def wallet_accounts(repository: str, minimum: int):
    location = os.environ.get("GENLAYER_STUDIONET_WALLET_FILE")
    if not location:
        raise AssertionError("GENLAYER_STUDIONET_WALLET_FILE is required")
    path = Path(location).expanduser().resolve(strict=True)
    repository_root = Path(__file__).resolve().parents[1]
    if path == repository_root or repository_root in path.parents:
        raise AssertionError("StudioNet wallet material must be outside the repository")
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle.get("schema") != "genlayer-studionet-wallet-bundle/v1":
        raise AssertionError("unexpected wallet-bundle schema")
    if bundle.get("repository") != repository:
        raise AssertionError("wallet bundle belongs to another repository")
    entries = bundle.get("accounts")
    if not isinstance(entries, list) or len(entries) < minimum:
        raise AssertionError("wallet bundle does not contain enough unique roles")
    accounts = []
    declared: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("private_key"), str):
            raise AssertionError("invalid wallet entry")
        account = create_account(entry["private_key"])
        address = str(account.address).lower()
        if str(entry.get("address", "")).lower() != address:
            raise AssertionError("wallet address does not match its private key")
        accounts.append(account)
        declared.append(address)
    if len(set(declared)) != len(declared):
        raise AssertionError("wallet bundle reuses an address")
    return accounts


def ok(receipt: dict[str, Any]) -> dict[str, Any]:
    assert tx_execution_succeeded(receipt), json.dumps(receipt, default=str)
    assert receipt.get("status_name") == TransactionStatus.FINALIZED.value
    assert receipt.get("result_name") in (None, "AGREE", "MAJORITY_AGREE")
    assert receipt.get("tx_execution_result_name") in (None, "FINISHED_WITH_RETURN")
    return receipt


def _rpc(method: str, params: list[Any]) -> Any:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(8):
        try:
            call = request.Request(
                STUDIONET_RPC,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Codex-GenLayer-Audit/1.0",
                },
            )
            with request.urlopen(call, timeout=30) as response:
                decoded = json.loads(response.read().decode("utf-8"))
            if decoded.get("error"):
                raise AssertionError(json.dumps(decoded["error"], sort_keys=True))
            return decoded["result"]
        except (error.HTTPError, error.URLError, TimeoutError, AssertionError) as exc:
            last_error = exc
            if attempt == 7:
                break
            time.sleep(6)
    raise AssertionError(f"StudioNet RPC verification failed: {last_error}")


def source_schema_proof(address: str, source_path: Path, required_methods: set[str]) -> dict[str, Any]:
    local_source = source_path.read_bytes()
    deployed_source = base64.b64decode(_rpc("gen_getContractCode", [address]), validate=True)
    assert deployed_source == local_source
    schema = _rpc("gen_getContractSchema", [address])
    assert isinstance(schema, dict) and isinstance(schema.get("methods"), dict)
    methods = set(schema["methods"])
    assert required_methods <= methods
    return {
        "source_sha256": hashlib.sha256(local_source).hexdigest(),
        "deployed_source_sha256": hashlib.sha256(deployed_source).hexdigest(),
        "schema_methods_verified": sorted(required_methods),
    }


def emit_record(
    repository: str,
    batch: str,
    address: str,
    deploy_receipt: dict[str, Any],
    setup_receipts: list[dict[str, Any]],
    intelligent_receipt: dict[str, Any],
    accounts: list[Any],
    proof: dict[str, Any],
    observed: dict[str, Any],
) -> None:
    record = {
        "schema": "genlayer-intelligent-contract-deployment/v2",
        "network": {"name": "studionet", "chain_id": 61999, "rpc": STUDIONET_RPC},
        "repository": repository,
        "batch": batch,
        "contract_address": address,
        "deployment_transaction_hash": deploy_receipt["hash"],
        "setup_transaction_hashes": [item["hash"] for item in setup_receipts],
        "intelligent_transaction_hash": intelligent_receipt["hash"],
        "wallet_addresses": [str(account.address) for account in accounts],
        "wallet_policy": "repository-specific disposable bundle outside workspace; no cross-repository reuse",
        "source": proof,
        "verification": {
            "status": "FINALIZED",
            "execution_success": True,
            "latest_final_readback": True,
            "deployed_source_exact": True,
            "schema_read": True,
            "observed": observed,
        },
    }
    print("STUDIONET_RECORD=" + json.dumps(record, sort_keys=True, default=str))
