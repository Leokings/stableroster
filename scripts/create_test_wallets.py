"""Generate fresh disposable test wallets; never print a private key.

Run only after release authorization. The output's parent must already have
owner-only permissions (NTFS ACL on Windows); keep it outside this workspace.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from genlayer_py import create_account


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    workspace = root.parent
    destination = args.output.resolve()
    if destination == workspace or workspace in destination.parents:
        raise SystemExit("Wallet material must stay outside the GenLayer workspace")
    if not destination.parent.is_dir() or destination.exists():
        raise SystemExit("Require a protected existing parent and a new output file")
    repository = root.name.lower()
    count = {"evidencecircuit": 1, "stableroster": 6}[repository]
    historical = json.loads((root / "deployments" / "historical" / "studionet-v1.json").read_text())
    forbidden = {value.lower() for value in historical.get("wallet_addresses", [])}
    accounts = [create_account() for _ in range(count)]
    addresses = [str(account.address).lower() for account in accounts]
    if len(set(addresses)) != count or forbidden.intersection(addresses):
        raise SystemExit("Fresh-wallet uniqueness check failed")
    bundle = {
        "schema": "genlayer-studionet-wallet-bundle/v1",
        "repository": repository,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "accounts": [{"address": str(account.address),
                      "private_key": "0x" + account.key.hex().removeprefix("0x")}
                     for account in accounts],
    }
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(bundle, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"repository": repository, "wallet_file": str(destination),
                      "wallet_addresses": [str(account.address) for account in accounts]}))


if __name__ == "__main__":
    main()
