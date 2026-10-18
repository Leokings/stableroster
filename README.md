# StableRoster v2

A reusable GenLayer bilateral pairing primitive: validators independently rank
fit under a frozen policy, deterministic Gale-Shapley creates stable pairs, and
each paired wallet must explicitly accept before a roster becomes SEALED.

Status (2026-10-18): v2 is deployed and verified on StudioNet. The fresh live
suite passed both lifecycle tests plus a separate runtime probe. Five cases
cover SEALED, DECLINED, WITHDRAWN, profile injection and real-time EXPIRED.
All 24 primary transactions finalized: 14 successful executions and 10 expected
rejections. The repository's public-access release check is still pending.

- [Inspect the live contract in StudioNet](https://studio.genlayer.com/?import-contract=0xF7f5A3e8a80177dcc5BF24810303c9010101CcA0)
- [Inspect its address and transactions](https://explorer-studio.genlayer.com/address/0xF7f5A3e8a80177dcc5BF24810303c9010101CcA0)
- [Deployed source, pinned to its source commit](https://github.com/Leokings/stableroster/blob/6b6d17b50162cebeae7b14cdbb4dcca3fdc7b2ab/contracts/stable_roster.py)
- [Release proof with actual receipts, votes and final records](deployments/studionet.json)

## Mechanism and lifecycle

Up to eight profiles on each side, a public compatibility policy, and a finite
response deadline are frozen. Validators agree on complete integer preference
permutations. Code, not the model, chooses the stable matching and lifecycle.

```text
Public profiles + frozen policy -> preference consensus -> Gale-Shapley pairs
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

This is a standalone MIT contract, not a hosted frontend. Copy the source and
configure your own cohorts and policy. All submitted text and responses are
permanently public. Use synthetic profiles for experiments.

## Inspect completed cases without a wallet

With Python 3.12+:

```text
python -m pip install -r requirements.txt
python scripts/verify_studionet.py
```

The verifier performs only public reads: chain ID, exact deployed source,
all seven interface methods, every final case, finalized execution outcomes
and actual vote maps. It neither loads a wallet nor submits a transaction.
StudioNet state can be reset; a future unavailable record is not new live proof.

| Case | Final public state |
| --- | --- |
| sealed | SEALED, all four paired wallets accepted |
| declined | DECLINED |
| withdrawn | WITHDRAWN |
| injection | WITHDRAWN, expected topic pairs/rankings retained before withdrawal |
| expiry | EXPIRED, late response rejected and unrelated caller closed it |

The six fresh test wallets were controlled by one test operator; this proves
wallet authorization, not six independent people. Native consensus was
MAJORITY_AGREE; actual idle/disagree votes are preserved, not called unanimous.
Configured model names do not prove heterogeneous independence or fallback use.

## Local verification

GenVM lint and strict typechecking pass. Local checks: 25 direct contract tests,
4 five-validator GLSim lifecycle scenarios and 15 offline tooling tests.
Mocked local model responses are distinct from the real-model live suite.

Use separate terminals for the final two commands:

```text
genvm-lint check contracts/stable_roster.py
genvm-lint typecheck contracts/stable_roster.py --strict
pytest tests/direct tests/tooling -v
python tests/run_glsim.py --port 4068 --validators 5 --no-browser
gltest tests/integration -v -s --network localnet --rpc-url http://127.0.0.1:4068/api
```

Public-network tests remain opt-in and require explicit release approval.
See deployments/README.md for preflight, external fresh wallets, resumable
checkpoints and the separately opt-in real-time expiry test.

## Compatibility, history and trust boundaries

v2 adds a required response_deadline parameter, expire_roster, immutable
terms_digest, closure timestamps and schema stableroster/roster/v2. Four-argument
v1 build calls must be migrated. The old v1 address is not an upgraded contract.

The August v1 proof is preserved in deployments/historical/studionet-v1.json.
It stopped at AWAITING_RESPONSES and did not prove completed consent or expiry.
The current v2 proof is independent, with exact source bytes verified on-chain.

This contract moves no funds, fetches no sources, and establishes neither
real-world identity nor profile authenticity. Exact ranking consensus can
disagree on ambiguous profiles; no unvalidated fallback is silently accepted.
StudioNet checks are not production certification.

See AUDIT.md, DESIGN.md, SECURITY.md, SOURCE_POLICY.md, ORIGINALITY.md,
REVIEW_CHECKLIST.md and the copy/paste Portal fields in SUBMISSION.txt.
