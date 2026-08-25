import json
import os
from pathlib import Path

import pytest
from gltest import get_contract_factory
from gltest.types import TransactionHashVariant, TransactionStatus
from gltest.utils import extract_contract_address

from tests.studionet_support import emit_record, ok, source_schema_proof, wallet_accounts


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.environ.get("RUN_STUDIONET") != "1", reason="opt-in live StudioNet test"),
]


def test_studionet_stable_bilateral_roster():
    accounts = wallet_accounts("stableroster", 5)
    owner, left0, left1, right0, right1 = accounts[:5]
    source = Path(__file__).resolve().parents[2] / "contracts" / "stable_roster.py"
    factory = get_contract_factory(contract_file_path=source)
    deployed = ok(factory.deploy_contract_tx(args=[], account=owner, wait_transaction_status=TransactionStatus.FINALIZED))
    address = extract_contract_address(deployed)
    contract = factory.build_contract(address, account=owner)
    left = json.dumps([{"wallet": str(left0.address), "profile": "Seeks structured weekly data mentoring."}, {"wallet": str(left1.address), "profile": "Seeks design mentoring through project collaboration."}])
    right = json.dumps([{"wallet": str(right0.address), "profile": "Offers structured weekly data mentoring."}, {"wallet": str(right1.address), "profile": "Offers design mentoring through shared projects."}])
    roster_id = f"{str(owner.address).lower()}:SPRING"
    intelligent = ok(contract.build_roster(args=["spring", left, right, "Pair the explicitly compatible mentoring goals and produce complete preferences for both sides." ]).transact(wait_transaction_status=TransactionStatus.FINALIZED))
    state = contract.get_roster(args=[roster_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
    assert state["schema"] == "stableroster/roster/v1" and len(state["pairs"]) == 2
    proof = source_schema_proof(address, source, {"build_roster", "respond_pair", "partner_of"})
    emit_record("stableroster", "A", address, deployed, [], intelligent, accounts, proof, {"state": state["state"], "pairs": state["pairs"]})
