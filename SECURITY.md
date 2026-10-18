# Security — StableRoster v2

The 2026-10-18 review fixed malformed leader preferences passing raw Python
equality, indefinitely pending responses and acceptance-required zero wallets.
The fix also prevents an owner rewriting DECLINED/WITHDRAWN terminal records.
See AUDIT.md and the regression suite.

Controls: complete bounded preference permutations; true integer indexes only;
canonical equality of the leader and independently reproduced matrices; a
deterministic normalization backstop; unique nonzero cohort wallets; caller,
side/index and one-response guards; a maximum seven-day immutable deadline;
permissionless deterministic expiry; immutable terminal states and term digest.

The matching is stable under the agreed model-generated matrices, not proof of
participants' genuine preferences, identity, qualifications or optimal welfare.
Only the named wallet controls its on-chain response. A dishonest profile can
remain false even after validators consistently interpret its text.

Prompts treat profiles and policy as untrusted. Tests with mocks prove parsing
and validator rejection, not live prompt-injection resilience. Ambiguous
profiles/rank ties can cause exact-consensus disagreement; failed builds do not
write a pending roster or lock funds.

Expiry is available to anyone at the deadline but requires a transaction.
After the deadline no response or withdrawal can sneak in before the expiry
transaction. Integrators must use finalized successful receipts and final-state
reads, not assume that a provisional status or a locally computed pair suffices.

All calldata and storage are public; no confidential profiles or secrets.
Live test keys must be fresh and repository-specific, stored outside the repo,
and never printed or committed. No public-network deployment was run for v2.
