# Security - StableRoster v2

The 2026-10-18 review fixed malformed leader preferences passing raw Python
equality, indefinitely pending responses and acceptance-required zero wallets.
The fix also prevents rewriting DECLINED/WITHDRAWN terminal records.
See AUDIT.md and the regression suite.

Controls: complete bounded preference permutations; true integer indexes only;
canonical equality of the leader and independently reproduced matrices; a
deterministic normalization backstop; unique nonzero cohort wallets; caller,
side/index and one-response guards; a maximum seven-day immutable deadline;
permissionless deterministic expiry; immutable terminal states and terms digest.

The matching is stable under the agreed model-generated matrices, not proof of
participants' genuine preferences, identity, qualifications or optimal welfare.
Only the named wallet controls its on-chain response. A dishonest profile can
remain false even after validators consistently interpret its text.

Prompts treat profiles and policy as untrusted. Mocked tests prove parsing and
validator rejection. The fresh StudioNet suite also passed a legitimate
positive case and the listed profile-injection case with expected rankings.
This is limited fixture evidence, not general prompt-injection immunity.
Ambiguous profiles/rank ties can cause exact-consensus disagreement; failed
builds do not store a pending roster or lock funds.

Expiry is available to anyone at the deadline but requires a transaction.
After the deadline no response or withdrawal can sneak in before the expiry
transaction. The live suite proved a rejected late response and unrelated-wallet
expiry. Integrators must use finalized successful receipts and final-state
reads, not assume a provisional status or locally computed pair suffices.

All calldata and storage are public; no confidential profiles or secrets.
The live tests used six newly generated repository-specific disposable wallets,
stored in an ACL-restricted directory outside the repository; no keys are
published. All six were controlled by the test operator, not independent people.
The public verifier reads state without loading any wallet or submitting writes.

The public manifest strips provider configuration, retaining only bounded
provider/model names and actual votes. Those names are not proof of fallback
selection or heterogeneous independence. Native MAJORITY_AGREE is not unanimity.
StudioNet testing is not production certification or a persistence guarantee.
