# StudioNet v2 release evidence

Current deployment (2026-10-18): VERIFIED.
Studio: https://studio.genlayer.com/?import-contract=0xF7f5A3e8a80177dcc5BF24810303c9010101CcA0
Explorer: https://explorer-studio.genlayer.com/address/0xF7f5A3e8a80177dcc5BF24810303c9010101CcA0
Source: https://github.com/Leokings/stableroster/blob/6b6d17b50162cebeae7b14cdbb4dcca3fdc7b2ab/contracts/stable_roster.py

studionet.json binds exact source bytes, runner, commit and blob to the fresh
contract. It contains a runtime probe, five final cases, 24 primary receipts,
actual votes, expected failures, per-step reads and final records.
The wallet-free verifier independently rechecks live code/schema, each final
record, and every primary transaction's finalization, execution and vote map:

```text
python -m pip install -r requirements.txt
python scripts/verify_studionet.py
```

The main deployment's 14 successful and 10 expected failed executions are
distinct from the two successful runtime-probe transactions. Finalized alone
does not mean execution success. The suite passed two live lifecycle tests
and the separate probe test. Native consensus was MAJORITY_AGREE; the manifest
preserves idle/disagree votes instead of claiming unanimous agreement.

historical/studionet-v1.json preserves the old August build, which reached only
AWAITING_RESPONSES. It proves neither completed consent nor v2 protections.

## Authorized reproduction, not an automatic deployment instruction

A new deployment or public-network test requires explicit owner approval.
Do not rerun live writes just to inspect existing evidence.

1. Verify current official SDK/network/runner support and polling guidance.
   This release used StudioNet chain 61999 and genlayer-py 0.16.3. A finalized
   pinned-runtime probe preceded the main deployment.
2. Push a reviewed source commit and record its byte digest and git blob.
3. Use SIX fresh repository-specific disposable accounts: owner, four paired
   members and an unrelated expiry/unauthorized caller. Store their bundle
   outside the workspace in an ACL-restricted directory. Never print keys or
   reuse historical wallets. The fresh unfunded accounts worked on StudioNet.
4. Opt in with RUN_STUDIONET=1 and external GENLAYER_STUDIONET_WALLET_FILE;
   target tests/integration/test_studionet_smoke.py with --network studionet.
   These are process-local test settings, not committed environment files.
5. The main test covers SEALED, DECLINED, WITHDRAWN and profile injection,
   unauthorized/closed-state expected failures, source/schema and readbacks.
   Its two-hour response window is a fixture choice, not a network guarantee.
6. RUN_STUDIONET_TIMEOUT=1 additionally enables the real-time expiry test.
   Its frozen ten-minute window rejects a late response; an unrelated wallet
   expires the roster without an LLM call. Both tests share the primary address.
7. Stop on unexpected judgments or state. Do not reset a missed deadline or
   relabel an unexpected execution as an expected rejection.

The external bundle uses schema genlayer-studionet-wallet-bundle/v1,
repository stableroster. It contains secrets and is never public evidence.
Profiles are synthetic supplied text; no identity/authenticity is established.

## Resumable checkpoints and actual recovery

The journal saves consensus hashes before waiting for finality. Ignored
.studionet-runs/v2.json survives .artifacts cleanup. Original readbacks are
preserved and later resumed snapshots are labeled separately.

A timeout is PENDING. A bound rerun polls the existing hash. A finalized failed
execution stays FINALIZED_ERROR. A lost broadcast response becomes
SUBMISSION_UNCERTAIN and blocks automatic resubmission. SDK transport receipt
handling leaves a gap before the consensus hash is returned; this is not an
atomic broadcast/checkpoint guarantee. An exclusive lock prevents concurrent
runs. Never remove a lock without confirming the process and public state.

This release encountered HTTP 502 during a pre-sign nonce lookup for accept_3.
The operator checked latest and pending nonce zero, plus unchanged on-chain
PENDING state, before authorizing the narrowly scoped recovery helper.
The retained reconciliation records that evidence. It did not resend an
already-broadcast transaction. Read-only 429/502/503/504 retries are finite;
raw transaction submission is not retried automatically.

Finality polling is bounded at 100 attempts, six seconds apart; verify current
network guidance for future runs. Deadlines persist across resumes.

## Evidence boundaries

VERIFIED means the manifest's specific assertions passed, not production
certification. All six wallets were controlled by one operator. Model names
are receipt configuration, not proof of runtime fallback or independent errors.
StudioNet records may become unavailable after network resets.
No Bradbury deployment or Portal submission was part of this release.
