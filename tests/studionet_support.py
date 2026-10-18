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


def install_rpc_timeouts():
    """Bound the pinned SDK's otherwise unbounded requests transport in this process."""
    import requests
    if getattr(requests.sessions.Session.request, "_release_bounded", False):
        return
    original = requests.sessions.Session.request

    def bounded(session, method, url, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = (10, 45)
        payload = kwargs.get("json", {})
        rpc_method = payload.get("method") if isinstance(payload, dict) else None
        safe_read = rpc_method in {
            "eth_chainId", "eth_gasPrice", "eth_getTransactionCount",
            "eth_getTransactionReceipt", "eth_getTransactionByHash",
            "eth_getBlockByNumber", "eth_getCode", "eth_call",
            "gen_call", "gen_getContractCode", "gen_getContractSchema",
            "gen_getContractSchemaForCode",
        }
        for attempt in range(3):
            try:
                response = original(session, method, url, **kwargs)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                if not safe_read or attempt == 2:
                    raise
            else:
                if not safe_read or getattr(response, "status_code", 200) not in (429, 502, 503, 504) or attempt == 2:
                    return response
            time.sleep(2 ** (attempt + 1))
        raise AssertionError("unreachable_transport_retry")

    bounded._release_bounded = True
    requests.sessions.Session.request = bounded


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
    assert tx_execution_succeeded(receipt), f"execution_failed: {receipt.get('hash')} / {receipt.get('status_name')}"
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
