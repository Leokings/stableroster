import json
from datetime import datetime, timezone


POLICY = "Pair people by compatible goals and complementary experience while respecting every complete preference order."
PREFS = {"left_preferences": [[0, 1], [1, 0]], "right_preferences": [[0, 1], [1, 0]]}
DEADLINE = int(datetime(2026, 8, 26, 12, tzinfo=timezone.utc).timestamp())


def _profiles(left_wallets, right_wallets):
    left = [{"wallet": str(left_wallets[0]), "profile": "Seeks data mentoring and prefers a structured weekly session."}, {"wallet": str(left_wallets[1]), "profile": "Seeks design mentoring and prefers project-based collaboration."}]
    right = [{"wallet": str(right_wallets[0]), "profile": "Offers data mentoring through structured weekly exercises."}, {"wallet": str(right_wallets[1]), "profile": "Offers design mentoring through project-based collaboration."}]
    return json.dumps(left), json.dumps(right)


def _build(contract, vm, owner, left_wallets, right_wallets):
    left, right = _profiles(left_wallets, right_wallets)
    vm.sender = owner
    vm.mock_llm(r".*Produce complete bilateral preference rankings.*", json.dumps(PREFS))
    return contract.build_roster("spring", left, right, POLICY, DEADLINE)


def test_gale_shapley_pairs_stably(contract, direct_vm, direct_alice, direct_bob, direct_charlie, direct_accounts):
    extra = direct_accounts[3]
    roster_id = _build(contract, direct_vm, direct_alice, [direct_bob, direct_charlie], [extra, direct_accounts[4]])
    assert contract.partner_of(roster_id, "LEFT", 0) == 0
    assert contract.partner_of(roster_id, "LEFT", 1) == 1


def test_every_paired_wallet_must_accept(contract, direct_vm, direct_alice, direct_bob, direct_charlie, direct_accounts):
    rights = [direct_accounts[3], direct_accounts[4]]
    roster_id = _build(contract, direct_vm, direct_alice, [direct_bob, direct_charlie], rights)
    for side, index, wallet in [("LEFT", 0, direct_bob), ("LEFT", 1, direct_charlie), ("RIGHT", 0, rights[0]), ("RIGHT", 1, rights[1])]:
        direct_vm.sender = wallet
        contract.respond_pair(roster_id, side, index, True)
    assert contract.is_fully_accepted(roster_id) is True


def test_decline_closes_roster(contract, direct_vm, direct_alice, direct_bob, direct_charlie, direct_accounts):
    roster_id = _build(contract, direct_vm, direct_alice, [direct_bob, direct_charlie], [direct_accounts[3], direct_accounts[4]])
    direct_vm.sender = direct_bob
    contract.respond_pair(roster_id, "LEFT", 0, False)
    assert contract.get_roster(roster_id)["state"] == "DECLINED"


def test_incomplete_preference_rejected(contract, direct_vm, direct_alice, direct_bob, direct_charlie, direct_accounts):
    left, right = _profiles([direct_bob, direct_charlie], [direct_accounts[3], direct_accounts[4]])
    direct_vm.sender = direct_alice
    direct_vm.mock_llm(r".*Produce complete bilateral preference rankings.*", json.dumps({"left_preferences": [[0], [1, 0]], "right_preferences": [[0, 1], [1, 0]]}))
    with direct_vm.expect_revert("[LLM_ERROR] incomplete_left_ranking"):
        contract.build_roster("bad", left, right, POLICY, DEADLINE)
