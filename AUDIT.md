# StableRoster v2 remediation review — 2026-10-18

Scope: local contracts/stable_roster.py, tests, release tooling and documentation
on branch codex/fix-review-blockers. No push, deployment, visibility change or
Portal submission was performed.

Current source SHA-256:
cc0034a745873b45640f4abd1cfecf0f139c13200fd3509994aa1c3109719527

Git blob: 293e5fd407ca3ed2cf3bd49aca46bc9fef2154f7
Base commit: 07d8732e35a5e300246158e57ee3a2ceb7de76f2
Changes remain uncommitted. This blob identifier is not a pushed release commit.

## Findings and fixes

| Finding | Severity | Local resolution |
| --- | --- | --- |
| SR-1: raw Python equality accepted Boolean/float preference indexes | Medium | Validate the leader with the exact schema and true-integer permutations, compare canonical normalized matrices, validate again before storage |
| SR-2: member responses could remain pending indefinitely | Medium | Required immutable future deadline, maximum seven days; exact-boundary response/withdrawal guard and permissionless deterministic expire_roster |
| SR-3: acceptance-required zero wallet allowed | Low | Reject zero and duplicate wallets before semantic work |
| SR-4: owner could overwrite a declined/withdrawn terminal record | Additional hardening | All four terminal states reject later response/withdrawal/expiry; closure timestamps preserve the result |
| Old live proof never completed bilateral consent | Review blocker | Full local lifecycle checks and new opt-in live tests prepared; fresh live execution still required |
| Private repository / unpushed fixes | Evidence blocker | Preserved pending owner approval |

Added immutable terms_digest and bounded record serialization. The fifth
response_deadline argument and roster/v2 schema are intentional breaking
changes; existing v1 clients and addresses must not be presented as updated.

## Local verification

- GenVM AST lint and SDK validation: PASS.
- Strict Pyright: PASS, zero diagnostics.
- Direct contract tests: 25 PASS, including forged Boolean/float/extra/missing
  rankings, all 16 two-by-two preference profiles, zero address, deadline
  boundaries, permissionless expiry, authorization and immutable terminal states.
- GLSim: 4 PASS with five mocked validators for each build; complete SEALED,
  DECLINED, WITHDRAWN and EXPIRED lifecycles, unauthorized/replay/late-response/
  terminal-overwrite expected rejections, final-state and digest readbacks.
- Offline journal tests: 11 PASS; persist-before-wait, pending resume, source/
  request binding, uncertain broadcast, finalized failure handling, concurrent
  lock, network guard and checkpoint survival of artifact cleanup.

Local Python and mocked models do not prove live GenVM compatibility, actual
ranking quality or heterogeneous-model prompt-injection resistance.
The refreshed opt-in StudioNet tests, including the additional real-time expiry
case, have NOT run. Expiry is permissionless but requires a transaction.

## History and readiness gates

docs/history/AUDIT_2026-08-25.md preserves the old audit; its no-blockers statement
is superseded. deployments/historical/studionet-v1.json records an old positive
build reaching AWAITING_RESPONSES only. It never proved acceptance or timeout.

Technical readiness: PASS for scoped local remediation; live runtime and
real-model/finite lifecycle proof still pending, not production-certified.
Distinctiveness: PASS against the 22 prior submissions and EvidenceCircuit,
especially distinct from FlowDispatch max-flow. No global novelty claim.
Evidence readiness: FAIL until the approved pushed/public source and fresh live
manifest exist. deployments/studionet.json explicitly says NOT_DEPLOYED.

Follow REVIEW_CHECKLIST.md and deployments/README.md before release. Preserve
expected failures, actual votes, every address and final-state readback; do not
call a built-but-unaccepted roster a completed consent demonstration.
