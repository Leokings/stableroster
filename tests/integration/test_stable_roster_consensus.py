import json
from pathlib import Path
from gltest import get_contract_factory, get_validator_factory
from gltest.accounts import create_accounts
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus
from gltest.utils import extract_contract_address


def _ok(receipt):
    assert tx_execution_succeeded(receipt), json.dumps(receipt, default=str)


def test_five_validator_stable_pairing_flow():
    owner, left0, left1, right0, right1 = create_accounts(5)
    factory = get_contract_factory(contract_file_path=Path(__file__).resolve().parents[2] / "contracts" / "stable_roster.py")
    receipt = factory.deploy_contract_tx(args=[], account=owner, wait_transaction_status=TransactionStatus.FINALIZED)
    _ok(receipt)
    contract = factory.build_contract(extract_contract_address(receipt), account=owner)
    left = json.dumps([{"wallet": str(left0.address), "profile": "Seeks data mentoring in a structured weekly session."}, {"wallet": str(left1.address), "profile": "Seeks design mentoring through project collaboration."}])
    right = json.dumps([{"wallet": str(right0.address), "profile": "Offers structured data mentoring every week."}, {"wallet": str(right1.address), "profile": "Offers design mentoring through shared projects."}])
    response = {"left_preferences": [[0, 1], [1, 0]], "right_preferences": [[0, 1], [1, 0]]}
    validators = get_validator_factory().batch_create_mock_validators(5, mock_llm_response={"nondet_exec_prompt": {"Produce complete bilateral preference rankings": json.dumps(response)}})
    context = {"validators": [v.to_dict() for v in validators], "genvm_datetime": "2026-08-25T12:00:00Z"}
    roster_id = f"{str(owner.address).lower()}:SPRING"
    receipt = contract.build_roster(args=["spring", left, right, "Pair compatible mentoring goals and complementary experience with complete preference orders."]).transact(transaction_context=context, wait_transaction_status=TransactionStatus.FINALIZED)
    _ok(receipt)
    assert contract.partner_of(args=[roster_id, "LEFT", 0]).call() == 0
