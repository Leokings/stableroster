"""Regression coverage for strict consensus types and finite roster acceptance."""

import copy
import itertools
import json
import sys
from datetime import datetime, timezone

import pytest


NOW = int(datetime(2026, 8, 25, 12, tzinfo=timezone.utc).timestamp())
DEADLINE = NOW + 3600
PREFERENCES = {"left_preferences": [[0, 1], [1, 0]], "right_preferences": [[0, 1], [1, 0]]}
POLICY = "Rank only compatible declared collaboration goals, using complete preferences."


def _build(contract, vm, accounts, zero_wallet=False, key="review", deadline=DEADLINE):
    left = [
        {"wallet": "0x" + "0" * 40 if zero_wallet else str(accounts[1]), "profile": "Seeks structured data collaboration."},
        {"wallet": str(accounts[2]), "profile": "Seeks project-based design collaboration."},
    ]
    right = [
        {"wallet": str(accounts[3]), "profile": "Offers structured data collaboration."},
        {"wallet": str(accounts[4]), "profile": "Offers project-based design collaboration."},
    ]
    vm.mock_llm(r".*Produce complete bilateral preference rankings.*", json.dumps(PREFERENCES))
    return contract.build_roster(key, json.dumps(left), json.dumps(right), POLICY, deadline)


def test_honest_validator_control(contract, direct_vm, direct_accounts):
    _build(contract, direct_vm, direct_accounts)
    assert direct_vm.run_validator() is True


def test_validator_rejects_boolean_preference_indexes(contract, direct_vm, direct_accounts):
    _build(contract, direct_vm, direct_accounts)
    forged = {"left_preferences": [[False, True], [True, False]], "right_preferences": [[False, True], [True, False]]}
    assert direct_vm.run_validator(leader_result=forged) is False


@pytest.mark.parametrize("kind", ["float", "extra", "missing", "duplicate", "different"])
def test_validator_rejects_other_malformed_or_disagreeing_rankings(contract, direct_vm, direct_accounts, kind):
    _build(contract, direct_vm, direct_accounts)
    forged = copy.deepcopy(PREFERENCES)
    if kind == "float":
        forged["left_preferences"][0] = [0.0, 1.0]
    elif kind == "extra":
        forged["winner"] = 1
    elif kind == "missing":
        forged["right_preferences"].pop()
    elif kind == "duplicate":
        forged["left_preferences"][0] = [0, 0]
    else:
        forged["right_preferences"][0] = [1, 0]
    assert direct_vm.run_validator(leader_result=forged) is False


def test_zero_address_cannot_be_an_acceptance_required_member(contract, direct_vm, direct_accounts):
    with direct_vm.expect_revert("invalid_wallet"):
        _build(contract, direct_vm, direct_accounts, zero_wallet=True)
    assert len(direct_vm._captured_validators) == 0


def test_pending_roster_has_a_finite_response_deadline(contract, direct_vm, direct_accounts):
    roster_id = _build(contract, direct_vm, direct_accounts)
    direct_vm.warp("2099-01-01T00:00:00Z")
    direct_vm.sender = direct_accounts[1]
    with direct_vm.expect_revert("response_window_expired"):
        contract.respond_pair(roster_id, "LEFT", 0, True)


@pytest.mark.parametrize("offset", [-1, 0, 604801])
def test_invalid_deadlines_rejected_before_model_call(contract, direct_vm, direct_accounts, offset):
    with direct_vm.expect_revert("invalid_response_deadline"):
        _build(contract, direct_vm, direct_accounts, deadline=NOW + offset)
    assert len(direct_vm._captured_validators) == 0


def test_deadline_boundary_blocks_response_and_allows_permissionless_expiry(contract, direct_vm, direct_accounts):
    roster_id = _build(contract, direct_vm, direct_accounts)
    direct_vm.warp("2026-08-25T13:00:00Z")
    direct_vm.sender = direct_accounts[1]
    with direct_vm.expect_revert("response_window_expired"):
        contract.respond_pair(roster_id, "LEFT", 0, True)
    direct_vm.sender = direct_accounts[5]
    before = len(direct_vm._captured_validators)
    contract.expire_roster(roster_id)
    assert contract.get_roster(roster_id)["state"] == "EXPIRED"
    assert contract.is_fully_accepted(roster_id) is False
    assert len(direct_vm._captured_validators) == before


def test_expiry_is_not_available_early(contract, direct_vm, direct_accounts):
    roster_id = _build(contract, direct_vm, direct_accounts)
    direct_vm.sender = direct_accounts[5]
    with direct_vm.expect_revert("response_window_open"):
        contract.expire_roster(roster_id)


@pytest.mark.parametrize("terminal", ["SEALED", "DECLINED", "WITHDRAWN", "EXPIRED"])
def test_terminal_states_are_final(contract, direct_vm, direct_alice, direct_accounts, terminal):
    roster_id = _build(contract, direct_vm, direct_accounts)
    digest = contract.get_roster(roster_id)["terms_digest"]
    if terminal == "SEALED":
        for side, index, wallet in [("LEFT", 0, direct_accounts[1]), ("LEFT", 1, direct_accounts[2]), ("RIGHT", 0, direct_accounts[3]), ("RIGHT", 1, direct_accounts[4])]:
            direct_vm.sender = wallet
            contract.respond_pair(roster_id, side, index, True)
    elif terminal == "DECLINED":
        direct_vm.sender = direct_accounts[1]
        contract.respond_pair(roster_id, "LEFT", 0, False)
    elif terminal == "WITHDRAWN":
        contract.withdraw_roster(roster_id, "The owner canceled the proposed collaboration.")
    else:
        direct_vm.warp("2026-08-25T13:00:00Z")
        direct_vm.sender = direct_accounts[5]
        contract.expire_roster(roster_id)
    original = contract.get_roster(roster_id)
    assert original["state"] == terminal
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("responses_closed"):
        contract.withdraw_roster(roster_id, "Attempt to overwrite the final state.")
    with direct_vm.expect_revert("responses_closed"):
        contract.expire_roster(roster_id)
    direct_vm.sender = direct_accounts[1]
    with direct_vm.expect_revert("responses_closed"):
        contract.respond_pair(roster_id, "LEFT", 0, True)
    assert contract.get_roster(roster_id) == original
    assert original["terms_digest"] == digest


def test_only_named_member_can_respond_and_cannot_replay(contract, direct_vm, direct_accounts):
    roster_id = _build(contract, direct_vm, direct_accounts)
    direct_vm.sender = direct_accounts[5]
    with direct_vm.expect_revert("only_member_wallet"):
        contract.respond_pair(roster_id, "LEFT", 0, True)
    direct_vm.sender = direct_accounts[1]
    contract.respond_pair(roster_id, "LEFT", 0, True)
    with direct_vm.expect_revert("already_responded"):
        contract.respond_pair(roster_id, "LEFT", 0, False)


def test_only_owner_can_withdraw(contract, direct_vm, direct_accounts):
    roster_id = _build(contract, direct_vm, direct_accounts)
    direct_vm.sender = direct_accounts[5]
    with direct_vm.expect_revert("only_owner"):
        contract.withdraw_roster(roster_id, "An unauthorized withdrawal attempt.")


def test_gale_shapley_has_no_blocking_pair_for_every_two_by_two_profile(contract):
    module = sys.modules[type(contract._instance).__module__]
    rankings = [(0, 1), (1, 0)]
    for rows in itertools.product(rankings, repeat=4):
        left, right = [list(row) for row in rows[:2]], [list(row) for row in rows[2:]]
        pairs = module._gale(left, right)
        partners_left = dict(pairs)
        partners_right = {r: l for l, r in pairs}
        assert len(pairs) == 2
        for l in range(2):
            for r in range(2):
                if partners_left[l] != r:
                    assert not (left[l].index(r) < left[l].index(partners_left[l]) and right[r].index(l) < right[r].index(partners_right[r]))
