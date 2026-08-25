# Originality audit

The final source was compared against 161 GenLayer
contract sources in the workspace. All twenty new target contracts were excluded
from the pre-existing comparison pool.

Nearest pre-existing source: `boxcomplete\contracts\manifest_recovery.py`

Combined structural score: `0.171086`

Token score: `0.275362`

AST score: `0.095443`

Nearest contract in this new set: `tradeoffatlas\contracts\tradeoff_atlas.py` with combined
score `0.278336`. That score reflects shared safe GenLayer
boilerplate. The mechanisms differ materially:

- This repository: Consensus produces complete preference matrices for two cohorts; deterministic Gale-Shapley matching creates pairs that require member responses.
- Other repository: Consensus emits a bounded score vector for every option; deterministic dominance pruning retains the complete non-dominated frontier.

The two do not share the same semantic input, deterministic algorithm, storage
record, state lifecycle, or decision views. Exact source SHA-256 values are also
unique across all twenty repositories. The complete machine-readable reports are
`review-tools/twenty-originality-audit.json` and
`review-tools/twenty-pairwise-audit.json` at the workspace level.

Similarity scoring is a review aid, not a guarantee of a human review outcome.
