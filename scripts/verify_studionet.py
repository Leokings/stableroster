"""Read-only verification of the published StudioNet release. No wallet or key."""

import base64
import hashlib
import json
from pathlib import Path
import sys
import time

from release_readonly import read_public, rpc


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "deployments" / "studionet.json").read_text())
    assert manifest["status"] == "VERIFIED"
    assert int(rpc("eth_chainId", []), 16) == manifest["network"]["chain_id"]
    code = base64.b64decode(rpc("gen_getContractCode", [manifest["contract_address"]]), validate=True)
    assert hashlib.sha256(code).hexdigest() == manifest["source"]["source_sha256"]
    assert code == (root / manifest["source"]["path"]).read_bytes()
    schema = rpc("gen_getContractSchema", [manifest["contract_address"]])
    assert set(manifest["verification"]["schema_methods"]) <= set(schema["methods"])
    sender = manifest["wallet_addresses"][0]
    for case in manifest["cases"]:
        state = read_public(manifest["contract_address"], case["method"], case["args"], sender)
        assert json.dumps(state, sort_keys=True) == json.dumps(case["expected_final_state"], sort_keys=True), case["name"]
        print("Final-state readback: " + case["name"] + " PASS", flush=True)
        time.sleep(1)
    for transaction in manifest["transactions"]:
        actual = rpc("eth_getTransactionByHash", [transaction["transaction_hash"]])
        assert actual["status"] == "FINALIZED"
        leader = actual["consensus_data"]["leader_receipt"]
        if isinstance(leader, list):
            leader = leader[0]
        assert (leader["execution_result"] == "SUCCESS") == transaction["execution_success"]
        assert actual["consensus_data"].get("votes", {}) == transaction["votes"]
        print("Finalized receipt: " + transaction["step"] + " PASS", flush=True)
        time.sleep(1)
    print("VERIFIED: exact live source/schema, every final case and transaction; no wallet used.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Verification failed: " + type(error).__name__, file=sys.stderr)
        raise SystemExit(1) from None
