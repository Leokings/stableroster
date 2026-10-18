"""Export sanitized public evidence only after all required live checks passed."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys


def summarize_step(name, entry):
    receipt = entry["receipt"]
    assert receipt["status_name"] == "FINALIZED"
    leaders = receipt.get("consensus_data", {}).get("leader_receipt", [])
    if isinstance(leaders, dict):
        leaders = [leaders]
    execution = leaders[0].get("execution_result")
    expected_error = entry["request"].get("expected_error")
    if expected_error:
        assert execution != "SUCCESS" and expected_error in json.dumps(receipt)
    else:
        assert execution == "SUCCESS"
    nodes = []
    candidates = leaders + receipt.get("consensus_data", {}).get("validators", [])
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        config = candidate.get("node_config") or {}
        profiles = {}
        for field in ("primary_model", "secondary_model"):
            model = config.get(field)
            if isinstance(model, dict):
                profiles[field] = {key: model[key] for key in ("provider", "model")
                                   if isinstance(model.get(key), str)}
        nodes.append({"address": config.get("address"), "mode": candidate.get("mode"),
                      "vote": candidate.get("vote"), "execution_result": candidate.get("execution_result"),
                      "configured_models": profiles})
    result = {
        "step": name, "transaction_hash": entry["transaction_hash"],
        "expected_outcome": "EXPECTED_FAILURE" if expected_error else "SUCCESS",
        "expected_error": expected_error, "status": receipt["status_name"],
        "execution_success": execution == "SUCCESS", "leader_execution": execution,
        "consensus_result": receipt.get("result_name"),
        "votes": receipt.get("consensus_data", {}).get("votes", {}),
        "participants": nodes, "request": entry["request"],
        "explorer": "https://explorer-studio.genlayer.com/tx/" + entry["transaction_hash"],
    }
    if "final_state_readback" in entry:
        result["post_step_final_readback"] = entry["final_state_readback"]
    if entry.get("resumed_readbacks"):
        result["later_resumed_readbacks"] = entry["resumed_readbacks"]
    return result


def export(root, source_commit):
    repository = root.name.lower()
    journal = json.loads((root / ".studionet-runs" / "v2.json").read_text())
    probe = json.loads((root / ".studionet-runs" / "probe.json").read_text())
    assert journal["status"] == probe["status"] == "VERIFIED"
    required = ({"positive", "negative", "missing", "not_missing", "not_refuted", "injection"}
                if repository == "evidencecircuit" else
                {"sealed", "declined", "withdrawn", "injection", "expiry"})
    assert required <= set(journal["observed"]["cases"])
    if repository == "stableroster":
        assert journal["observed"]["expiry_proof"] == "VERIFIED"
    source_path = "contracts/" + ("evidence_circuit.py" if repository == "evidencecircuit" else "stable_roster.py")
    source = (root / source_path).read_bytes()
    committed = subprocess.check_output(["git", "show", source_commit + ":" + source_path], cwd=root)
    assert source == committed, "live source differs from the pushed source commit"
    digest = hashlib.sha256(source).hexdigest()
    assert journal["binding"]["source_sha256"] == journal["source"]["deployed_source_sha256"] == digest
    address = journal["observed"]["contract_address"]
    # Recheck the complete public interface, not just the expiry test's subset.
    sys.path.insert(0, str(root))
    from tests.studionet_support import source_schema_proof
    final_source_proof = source_schema_proof(address, root / source_path, {
        "build_roster", "respond_pair", "withdraw_roster", "expire_roster",
        "get_roster", "partner_of", "is_fully_accepted",
    })
    transactions = [summarize_step(name, entry) for name, entry in journal["steps"].items()]
    cases = []
    for name, observed in journal["observed"]["cases"].items():
        if repository == "evidencecircuit":
            final = journal["steps"][name]["final_state_readback"]
            method, args = "get_run", [observed["run_id"]]
        else:
            step = {"sealed": "closed_withdrawal_sealed", "declined": "closed_withdrawal_declined",
                    "withdrawn": "closed_withdrawal_withdrawn", "injection": "withdraw_injection",
                    "expiry": "expire"}[name]
            final = journal["steps"][step]["final_state_readback"]
            method, args = "get_roster", [observed["roster_id"]]
        cases.append({"name": name, "method": method, "args": args, "expected_final_state": final})
    versions = {name: importlib.metadata.version(name) for name in
                ("genlayer-py", "genlayer-test", "genvm-linter", "pytest", "pyright")}
    manifest = {
        "schema": "genlayer-intelligent-contract-release/v3", "repository": "Leokings/" + repository,
        "contract_version": "v2", "status": "VERIFIED", "verified_at": datetime.now(timezone.utc).isoformat(),
        "network": {"name": "studionet", "chain_id": 61999, "rpc": "https://studio.genlayer.com/api"},
        "source": {"path": source_path, "commit": source_commit, "source_sha256": digest,
                   "deployed_source_sha256": digest,
                   "git_blob": subprocess.check_output(["git", "rev-parse", source_commit + ":" + source_path], cwd=root, text=True).strip(),
                   "runner": json.loads(source.splitlines()[0].decode()[2:])["Depends"],
                   "url": "https://github.com/Leokings/" + repository + "/blob/" + source_commit + "/" + source_path},
        "constructor_args": [], "contract_address": address,
        "studio": "https://studio.genlayer.com/?import-contract=" + address,
        "explorer": "https://explorer-studio.genlayer.com/address/" + address,
        "deployment_transaction_hash": journal["steps"]["deploy"]["transaction_hash"],
        "wallet_addresses": journal["binding"]["wallet_addresses"],
        "wallet_policy": "Fresh per-repository disposable accounts generated for this release; no historical wallet reuse",
        "transactions": transactions, "cases": cases,
        "runtime_probe": {"contract_address": probe["observed"]["contract_address"],
                          "source": probe["source"], "observed": probe["observed"],
                          "transactions": [summarize_step(name, entry) for name, entry in probe["steps"].items()]},
        "reconciliations": journal.get("reconciliations", []),
        "toolchain": versions,
        "verification": {"all_required_live_cases": True, "finalized_execution_checked": True,
                         "expected_failures_checked": True, "latest_final_readbacks": True,
                         "deployed_source_exact": True, "schema_methods": final_source_proof["schema_methods_verified"]},
        "boundaries": [
            "Caller-supplied synthetic public packets/profiles; no independent external-source authentication",
            "No funds, identity or legal attestation",
            "Votes are recorded as returned, including idle voters; this is not a fabricated 5/5 claim",
            "Configured model names do not prove runtime fallback selection or heterogeneous independence",
            "StudioNet testing is not production certification; state persistence is not guaranteed",
            "Historical v1 evidence is preserved separately and does not prove v2",
        ],
    }
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = export(root, args.source_commit)
    destination = root / "deployments" / "studionet.json"
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": manifest["status"], "contract_address": manifest["contract_address"],
                      "cases": len(manifest["cases"]), "transactions": len(manifest["transactions"])}))


if __name__ == "__main__":
    main()
