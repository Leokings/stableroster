# StableRoster v2

A reusable GenLayer bilateral pairing primitive: validators independently rank
fit under a frozen policy, deterministic Gale–Shapley creates stable pairs, and
each paired wallet must explicitly accept before a roster becomes SEALED.

Status (2026-10-18): local remediation, not pushed or deployed. Lint and strict
typechecking pass; 25 direct contract tests, 4 five-validator GLSim lifecycle
scenarios and 11 offline journal tests pass. Local model responses are mocked.
The August v1 live proof stopped at AWAITING_RESPONSES; it proves no completed
consent or expiry flow and does not prove this changed source.

## Mechanism and lifecycle

Up to eight profiles on each side, a public compatibility policy, and a finite
response deadline are frozen. Validators agree on complete integer preference
permutations. Code, not the model, chooses the stable matching and lifecycle.

```text
Public profiles + frozen policy -> preference consensus -> Gale–Shapley pairs
AWAITING_RESPONSES -> SEALED | DECLINED | WITHDRAWN | EXPIRED
```

The model does not establish a participant's real preferences or identity.
Participants can reject a proposed pair. Stability means no blocking pair under
the agreed matrices; it does not mean global optimality or real-world fairness.

## Interface and first use

```python
build_roster(roster_key: str, left_profiles_json: str, right_profiles_json: str,
             pairing_policy: str, response_deadline: u256) -> str
respond_pair(roster_id: str, side: str, member_index: u256, accept: bool) -> None
withdraw_roster(roster_id: str, reason: str) -> None
expire_roster(roster_id: str) -> None
get_roster(roster_id: str) -> dict
partner_of(roster_id: str, side: str, member_index: u256) -> int
is_fully_accepted(roster_id: str) -> bool
```

1. Prepare each side as an array of {"wallet":"0x...","profile":"public text"}.
   Wallets must be valid, nonzero and unique across both cohorts.
2. Choose an absolute UTC epoch-second deadline strictly after the transaction's
   time and at most seven days ahead. Pass it as the required fifth argument.
3. Build the roster under your own key. The ID is lower-case owner address +
   ":" + upper-case key. Read the finalized v2 record, pairs and terms_digest.
4. Each paired wallet calls respond_pair with LEFT/RIGHT, its original cohort
   index and a true Boolean. Everyone paired must accept to reach SEALED.
   An unpaired member cannot respond; a single decline closes the entire roster.
5. Before the deadline, only the owner may withdraw a pending roster. At or
   after the deadline, responses and withdrawal are rejected; anyone may call
   expire_roster with no model call. Expiry is permissionless, not automatic:
   someone still has to submit that transaction.
6. SEALED, DECLINED, WITHDRAWN and EXPIRED are immutable terminal states.
   Wait for successful finalized receipts and read final state before relying
   on membership. is_fully_accepted is true only for SEALED.

For a wallet-free exercise run tests/direct/test_stable_roster.py and the
regression suite; inspect the four terminal lifecycles in
tests/integration/test_stable_roster_consensus.py. These are local simulations,
not a public live app. No current v2 public contract address exists.

## Local verification

Use Python 3.12+ and separate terminals for the last two commands:

```text
python -m pip install -r requirements.txt
genvm-lint check contracts/stable_roster.py
genvm-lint typecheck contracts/stable_roster.py --strict
pytest tests/direct tests/tooling -v
python tests/run_glsim.py --port 4068 --validators 5 --no-browser
gltest tests/integration -v -s --network localnet --rpc-url http://127.0.0.1:4068/api
```

Public-network tests remain opt-in and must not run without release approval.
See deployments/README.md for preflight, external fresh wallets, checkpoints and
the separately opt-in real-time expiry test.

## Compatibility and boundaries

v2 adds a required response_deadline parameter, expire_roster, immutable
terms_digest, closure timestamps and schema stableroster/roster/v2. Four-argument
v1 build calls must be migrated. Do not point consumers at v1 and claim the new
deadline or strict-consensus protections.

This MIT-licensed standalone contract is reusable without a frontend. It moves
no funds, fetches no sources, and establishes neither real-world identity nor
profile authenticity. All submitted profiles, policies and responses are public.
Exact ranking consensus can disagree on ambiguous profiles; no unvalidated
fallback ranking is silently accepted.

See AUDIT.md, DESIGN.md, SECURITY.md, SOURCE_POLICY.md, ORIGINALITY.md,
REVIEW_CHECKLIST.md and draft SUBMISSION.txt. The current deployment manifest
explicitly records NOT_DEPLOYED.
