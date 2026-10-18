"""Explicitly opt-in runner/client write-read compatibility probe."""

import os
from pathlib import Path

import pytest
from gltest import get_contract_factory
from gltest.types import TransactionHashVariant
from gltest.utils import extract_contract_address

from tests.studionet_journal import StudioJournal
from tests.studionet_support import ok, source_schema_proof, wallet_accounts


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.environ.get("RUN_STUDIONET") != "1", reason="opt-in live StudioNet probe"),
]


def test_studionet_runner_compatibility():
    root = Path(__file__).resolve().parents[2]
    repository = root.name.lower()
    accounts = wallet_accounts(repository, 1)
    source = root / "tests" / "fixtures" / "runner_probe.py"
    factory = get_contract_factory(contract_file_path=source)
    with StudioJournal(repository, source, accounts, path=root / ".studionet-runs" / "probe.json") as journal:
        deployed = ok(journal.transaction("deploy", accounts[0], []))
        address = extract_contract_address(deployed)
        contract = factory.build_contract(address, account=accounts[0])
        ok(journal.transaction("write", accounts[0], [17], address=address, method="set_value"))
        assert contract.get_value().call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL) == 17
        seen_at = contract.get_timestamp().call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
        assert isinstance(seen_at, str) and seen_at
        journal.readback("write", {"value": 17, "transaction_datetime": seen_at})
        proof = source_schema_proof(address, source, {"set_value", "get_value", "get_timestamp"})
        journal.finish(proof, {"contract_address": address, "value": 17, "transaction_datetime": seen_at})
