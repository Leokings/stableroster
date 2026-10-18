"""Full local roster lifecycles with five mocked validators, not live proof."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from gltest import get_contract_factory, get_validator_factory
from gltest.accounts import create_accounts
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionHashVariant, TransactionStatus
from gltest.utils import extract_contract_address


pytestmark = pytest.mark.integration
NOW = {"genvm_datetime": "2026-08-25T12:00:00Z"}
DEADLINE = int(datetime(2026, 8, 25, 13, tzinfo=timezone.utc).timestamp())
LATER = {"genvm_datetime": "2026-08-25T13:00:00Z"}


def _ok(receipt):
    assert receipt["status_name"] == TransactionStatus.FINALIZED.value
    assert tx_execution_succeeded(receipt), json.dumps(receipt, default=str)


def _rejected(receipt, code):
    assert receipt["status_name"] == TransactionStatus.FINALIZED.value
    assert not tx_execution_succeeded(receipt)
    assert code in json.dumps(receipt, default=str)


@pytest.mark.parametrize("terminal", ["SEALED", "DECLINED", "WITHDRAWN", "EXPIRED"])
def test_five_validator_stable_pairing_lifecycle(terminal):
    accounts = create_accounts(6)
    owner, left0, left1, right0, right1, outsider = accounts
    source = Path(__file__).resolve().parents[2] / "contracts" / "stable_roster.py"
    factory = get_contract_factory(contract_file_path=source)
    receipt = factory.deploy_contract_tx(args=[], account=owner, transaction_context=NOW,
        wait_transaction_status=TransactionStatus.FINALIZED)
    _ok(receipt)
    address = extract_contract_address(receipt)
    clients = [factory.build_contract(address, account=account) for account in accounts]
    contract = clients[0]
    left = json.dumps([{"wallet": str(left0.address), "profile": "Seeks structured weekly data mentoring."},
                       {"wallet": str(left1.address), "profile": "Seeks project-based design mentoring."}])
    right = json.dumps([{"wallet": str(right0.address), "profile": "Offers structured weekly data mentoring."},
                        {"wallet": str(right1.address), "profile": "Offers project-based design mentoring."}])
    response = {"left_preferences": [[0, 1], [1, 0]], "right_preferences": [[0, 1], [1, 0]]}
    validators = get_validator_factory().batch_create_mock_validators(5, mock_llm_response={
        "nondet_exec_prompt": {"Produce complete bilateral preference rankings": json.dumps(response)}})
    context = {**NOW, "validators": [v.to_dict() for v in validators]}
    roster_id = f"{str(owner.address).lower()}:SPRING"
    args = ["spring", left, right, "Pair compatible declared mentoring goals and complementary experience.", DEADLINE]
    _ok(contract.build_roster(args=args).transact(transaction_context=context,
        wait_transaction_status=TransactionStatus.FINALIZED))
    state = contract.get_roster(args=[roster_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
    assert state["schema"] == "stableroster/roster/v2"
    assert state["pairs"] == [[0, 0], [1, 1]]
    assert state["response_deadline"] == DEADLINE
    assert len(state["terms_digest"]) == 64
    assert contract.partner_of(args=[roster_id, "LEFT", 0]).call() == 0
    _rejected(contract.build_roster(args=args).transact(transaction_context=NOW,
        wait_transaction_status=TransactionStatus.FINALIZED), "roster_exists")
    _rejected(clients[5].respond_pair(args=[roster_id, "LEFT", 0, True]).transact(
        transaction_context=NOW, wait_transaction_status=TransactionStatus.FINALIZED), "only_member_wallet")
    _rejected(clients[5].expire_roster(args=[roster_id]).transact(transaction_context=NOW,
        wait_transaction_status=TransactionStatus.FINALIZED), "response_window_open")
    if terminal == "SEALED":
        for client, side, index in [(clients[1], "LEFT", 0), (clients[2], "LEFT", 1),
                                     (clients[3], "RIGHT", 0), (clients[4], "RIGHT", 1)]:
            _ok(client.respond_pair(args=[roster_id, side, index, True]).transact(
                transaction_context=NOW, wait_transaction_status=TransactionStatus.FINALIZED))
    elif terminal == "DECLINED":
        _ok(clients[1].respond_pair(args=[roster_id, "LEFT", 0, False]).transact(
            transaction_context=NOW, wait_transaction_status=TransactionStatus.FINALIZED))
    elif terminal == "WITHDRAWN":
        _ok(contract.withdraw_roster(args=[roster_id, "Owner canceled this proposed collaboration."]).transact(
            transaction_context=NOW, wait_transaction_status=TransactionStatus.FINALIZED))
    else:
        _rejected(clients[1].respond_pair(args=[roster_id, "LEFT", 0, True]).transact(
            transaction_context=LATER, wait_transaction_status=TransactionStatus.FINALIZED), "response_window_expired")
        _ok(clients[5].expire_roster(args=[roster_id]).transact(transaction_context=LATER,
            wait_transaction_status=TransactionStatus.FINALIZED))
    final = contract.get_roster(args=[roster_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL)
    assert final["state"] == terminal and final["closed_at"]
    assert final["terms_digest"] == state["terms_digest"]
    assert contract.is_fully_accepted(args=[roster_id]).call() is (terminal == "SEALED")
    _rejected(contract.withdraw_roster(args=[roster_id, "Cannot overwrite a terminal result."]).transact(
        transaction_context=LATER, wait_transaction_status=TransactionStatus.FINALIZED), "responses_closed")
    _rejected(clients[1].respond_pair(args=[roster_id, "LEFT", 0, True]).transact(
        transaction_context=LATER, wait_transaction_status=TransactionStatus.FINALIZED), "responses_closed")
    assert contract.get_roster(args=[roster_id]).call() == final
