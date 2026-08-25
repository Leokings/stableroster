# StableRoster

Bilateral stable roster construction.

Batch: A

## Why it is GenLayer-native

Consensus produces complete preference matrices for two cohorts; deterministic Gale-Shapley matching creates pairs that require member responses.

The LLM handles only the bounded semantic step. Deterministic contract code owns
the reusable algorithm, state transitions, access control, tie-breaking, and
views. One deployment supports many caller-keyed records; it is not tied to the
StudioNet fixture or one organization.

## Public interface

Write methods: `build_roster`, `respond_pair`, `withdraw_roster`

View methods: `get_roster`, `partner_of`, `is_fully_accepted`

## Verification

```text
pip install -r requirements.txt
genvm-lint check contracts/stable_roster.py
genvm-lint typecheck contracts/stable_roster.py --strict
pytest tests/direct -q
python tests/run_glsim.py --port 4000 --validators 5
gltest tests/integration -q --network localnet
```

The live smoke test is opt-in and requires a repository-specific wallet bundle
outside the repository. It waits for finalized receipts, reads `LATEST_FINAL`,
retrieves deployed source and schema from StudioNet, and fails unless the source
bytes exactly match this repository.

StudioNet contract: https://explorer-studio.genlayer.com/address/0x835D4992fc688AeAe043f0B30839BDB3132282D4

See `AUDIT.md`, `ORIGINALITY.md`, `SOURCE_POLICY.md`, `SECURITY.md`,
`SUBMISSION.md`, and `deployments/studionet.json` for the final evidence.

## Boundary

The contract moves no funds and does not establish identity, ownership,
professional authority, source authenticity, physical truth, or legal effect.
All caller inputs and calldata are public. Off-chain clients own authentication,
privacy, source curation, indexing, and the decision to rely on a result.
