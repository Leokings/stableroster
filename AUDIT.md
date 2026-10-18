# StableRoster v2 release review - 2026-10-18

Scope: contracts/stable_roster.py, tests, release tooling and documentation.
The owner approved pushing fixes, fresh StudioNet tests and public publication.
No Bradbury deployment or Portal submission is included.

Deployed source commit: 6b6d17b50162cebeae7b14cdbb4dcca3fdc7b2ab
Source SHA-256: cc0034a745873b45640f4abd1cfecf0f139c13200fd3509994aa1c3109719527
Git blob: 293e5fd407ca3ed2cf3bd49aca46bc9fef2154f7

## Findings and fixes

| Finding | Severity | Resolution |
| --- | --- | --- |
| SR-1: raw Python equality accepted Boolean/float preference indexes | Medium | Exact schema, true-integer permutations, canonical normalized comparison and deterministic backstop |
| SR-2: member responses could remain pending indefinitely | Medium | Immutable future deadline, maximum seven days, exact-boundary response/withdrawal guards and permissionless expire_roster |
| SR-3: acceptance-required zero wallet allowed | Low | Reject zero and duplicate wallets before semantic work |
| SR-4: owner could overwrite a declined/withdrawn terminal record | Additional hardening | All four terminal states reject later mutations; closure timestamps preserve the result |
| Old live proof never completed bilateral consent | Review blocker | Fresh v2 live suite completed consent, decline, withdrawal, injection and expiry cases |
| Private source / missing release evidence | Evidence blocker | Source and current proof pushed, repository public, all five evidence links checked anonymously |

Added immutable terms_digest and bounded record serialization. The fifth
response_deadline argument and roster/v2 schema are intentional breaking
changes; existing v1 clients and addresses must not be presented as updated.

## Local verification

- GenVM AST lint and SDK validation: PASS.
- Strict Pyright: PASS, zero diagnostics.
- Direct contract tests: 25 PASS, including forged Boolean/float/extra/missing
  rankings, all 16 two-by-two preference profiles, zero address, deadline
  boundaries, permissionless expiry, authorization and immutable terminal states.
- GLSim: 4 PASS with five mocked validators, covering all four terminal states.
- Offline tooling tests: 15 PASS, including checkpoint/resume, uncertain
  broadcast handling, nonce-recovery guards and secret-redacting proof export.
- Linux CI initially exposed a clock fixture defect: the harness updated the
  typed time but not raw message datetime. The cross-platform fixture now
  refreshes both. Contract logic and the existing assertions were not weakened.

## Live StudioNet verification

Contract: 0xF7f5A3e8a80177dcc5BF24810303c9010101CcA0
Studio: https://studio.genlayer.com/?import-contract=0xF7f5A3e8a80177dcc5BF24810303c9010101CcA0
Explorer: https://explorer-studio.genlayer.com/address/0xF7f5A3e8a80177dcc5BF24810303c9010101CcA0

Pinned runner: py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6
Chain ID: 61999. SDK: genlayer-py 0.16.3.
A separate runtime probe finalized deploy/write/read before the main deployment.

Both live lifecycle tests passed: five final cases, 24 primary transactions.
14 executions succeeded. Ten finalized errors were intentional: three
unauthorized responses, six terminal response/withdrawal replays and one late
response. All four paired fresh wallets accepted the SEALED case; decline and
owner withdrawal completed independently. The injection case retained the
expected topic pairs/rankings and was then withdrawn. The expiry case rejected
a response after its frozen deadline and an unrelated sixth wallet called
expire_roster successfully, with no model call for expiry.

Every final record and primary receipt was re-read by the wallet-free verifier.
Exact live source bytes, source digest, git blob and all seven public methods
were checked. deployments/studionet.json contains the actual receipt outcomes,
vote maps, bounded model metadata, per-step readbacks and final records.

A transient HTTP 502 occurred during nonce lookup BEFORE signing/broadcast of
accept_3. Public latest/pending nonce zero and the unmodified PENDING response
were independently checked. The manual, narrowly scoped reconciliation is
retained in the manifest; only then was its first broadcast submitted.
Read-only retries are finite. Transaction submission is never auto-retried.

Native consensus was MAJORITY_AGREE. Idle and disagree votes remain in the
proof; this is not a claim of unanimous agreement. Configured provider/model
names do not establish runtime fallback use or independent model failures.

## Trust boundaries and history

Tests use synthetic public profiles. The operator controlled all six fresh
disposable wallets. This demonstrates address-based authorization and specified
lifecycle behavior, not identity, truthful profiles, real preferences, or broad
prompt-injection immunity. There are no funds. Expiry is permissionless but
requires a transaction. StudioNet persistence and production safety are not
guaranteed by these tests.

docs/history/AUDIT_2026-08-25.md and deployments/historical/studionet-v1.json
preserve the old audit and old AWAITING_RESPONSES-only example. They are
historical, not evidence for this v2 code.

## Readiness gates

Technical readiness: PASS for the audited scope, local checks and listed
fresh live v2 scenarios. Not production-certified.
Distinctiveness: PASS against the recorded 22 prior submissions and
EvidenceCircuit, especially distinct from FlowDispatch's max-flow mechanism.
No exhaustive/global novelty claim.
Evidence readiness: PASS. The approved repository is public; all five form
links returned HTTP 200 without authentication. The pinned source fetched
anonymously matches the deployed byte hash. Source, current proof and finalized
outcomes are complete. GitHub release checks passed on proof commit
7fbfa64352796f52b731a519637e066e0d21fe74:
https://github.com/Leokings/stableroster/actions/runs/39170335613

The final Portal contribution remains an owner action. No points, acceptance
or weekly submission capacity are promised.
