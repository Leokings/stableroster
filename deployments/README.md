# Deployment evidence and approved-release procedure

Current v2: NOT_DEPLOYED. studionet.json is a readiness record, not proof.
historical/studionet-v1.json preserves August's exact-source positive build.
Its state was AWAITING_RESPONSES, so it proves neither bilateral completion nor
any new deadline, strict-type or terminal-state protection.

No live-network test ran during remediation. Do not deploy, push or change
visibility without the owner's approval.

## Preflight for a later authorized run

1. Verify current official SDK/network/runner support and polling guidance;
   probe the pinned runtime first. Local lint is not a live compatibility probe.
2. Review and push a source commit, recording the commit and blob hashes.
3. Provide SIX fresh repository-specific disposable accounts (owner, four
   members and an unrelated expiry/unauthorized caller), stored in an external
   wallet bundle. Do not reuse historical wallets. StudioNet needs no funding.
4. Only after approval, opt in with RUN_STUDIONET=1 and the external
   GENLAYER_STUDIONET_WALLET_FILE; target
   tests/integration/test_studionet_smoke.py with --network studionet.
5. The main test exercises SEALED, DECLINED and WITHDRAWN, unauthorized and
   closed-state expected failures, final-state reads and exact source/schema.
   It has a two-hour deadline to accommodate normal testing, not production
   network timing guarantees.
6. The additional real-time expiry test requires RUN_STUDIONET_TIMEOUT=1.
   It creates a ten-minute response window, waits finitely, rejects a late
   response, and expires from the unrelated sixth wallet without an LLM call.
   It reuses the primary deployment and appends its EXPIRY case to the same
   public journal. All lifecycle proofs therefore share one contract address.
7. Add/review real profile-injection and legitimate positive cases before
   release; existing mocked adversarial checks are not a live model safety
   certification. Stop on any unexpected judgment or state.

The external bundle schema is genlayer-studionet-wallet-bundle/v1, repository
stableroster, with an accounts array whose entries contain address and matching
private_key. No external bundle was opened or generated during this local fix.

## Resumable checkpoints

The journal uses verified hash-returning SDK calls and saves consensus hashes
before waiting for finality. Ignored .studionet-runs/v2.json survives gltest's
.artifacts cleanup. Original readbacks are preserved on resumed runs.

A timeout is PENDING. Repeating the same bound source/accounts/arguments polls
the existing hash; a finalized failed execution stays FINALIZED_ERROR, not
success. A lost broadcast response is SUBMISSION_UNCERTAIN and blocks automatic
resubmission until manual public nonce/transaction reconciliation. The SDK
waits for a transport receipt before returning the consensus hash; this gap is
explicitly not an atomic broadcast+checkpoint guarantee.

An exclusive lock blocks concurrent runs. After a crash, confirm no process is
active and reconcile transactions before removing a stale lock. Deadlines are
persisted so a resumed test does not silently change terms. If a live case
misses its response window, report that failure; do not silently reset its
deadline or relabel it successful.

Polls are bounded at 100 attempts, six seconds apart; check current network
guidance before enabling them. Inspect the public-only journal and assemble a
manifest with commit/blob/runner, source bytes, every receipt/vote, expected
failure labels and readbacks. VERIFIED denotes only listed assertions, not
production certification. Never overwrite historical evidence.
