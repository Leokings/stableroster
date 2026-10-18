# StableRoster v2 design

## Judgment and algorithm boundary

A caller freezes public left/right cohorts, a compatibility policy and a
deadline. The only semantic operation is a pair of complete ordered preference
matrices. Validators independently reproduce the matrices and compare the
canonical normalized JSON, including every index and field.

```json
{"left_preferences":[[0,1],[1,0]],"right_preferences":[[0,1],[1,0]]}
```

Each row must contain all opposing indexes exactly once, as true integers.
Boolean indexes, floats, duplicate/missing indexes, extra keys and changed
rankings are rejected. Deterministic execution normalizes the result again.
Nothing relies on Python's False == 0 or 1.0 == 1 equality behavior.

Left-proposing Gale–Shapley constructs the matching; stable means no unmatched
pair prefers each other over their assigned partners under these matrices.
Unequal cohort sizes are allowed and unmatched members do not block sealing.
The model cannot set balances, payouts or terminal outcomes.

## Consent and finite waiting

Schema stableroster/roster/v2 starts AWAITING_RESPONSES. Each paired wallet may
respond once, on its own cohort side/index, strictly before the response deadline.
All paired members accepting seals the roster; one rejection makes it DECLINED.
Only its owner may withdraw it while pending and before the deadline.

response_deadline is absolute UTC epoch seconds, checked against transaction
time from gl.message_raw["datetime"]. It must be future and within seven days.
At the exact deadline, responses/withdrawals are closed and permissionless
expire_roster becomes available, with no model call. Expiry requires a caller;
there is no autonomous scheduler. No funds are locked.

All four terminal states are final. The owner cannot overwrite a declined,
withdrawn, expired or sealed decision. closed_at records closure; withdrawal
reason and sealed_at are recorded for their respective transitions.

## Bounds and binding

One to eight members per side; unique nonzero 20-byte hex wallets; 12–800 ASCII
characters per profile; 20–2,500 characters per policy; 44-character keys.
Cohort JSON is capped at 10,000 characters before parsing and serialized records
at 32,768 characters. Matching makes at most left_count * right_count proposals.
Maps grow per roster but no transaction scans the entire registry.

terms_digest binds contract address, owner, roster ID, cohorts, policy and
deadline. It remains unchanged as responses arrive. The digest identifies
agreed terms, not the authenticity or truth of profiles.

## Migration and failure

New fifth build argument and v2 response schema are breaking changes.
Immutable v1 deployments need replacement, not an alleged in-place upgrade.
An invalid or unagreed model result rolls back the build; no partially built
roster is written. Exact ranking consensus may reduce liveness on ambiguous
profiles. Existing v1 proof is historical, and the new finite lifecycle still
needs authorized live GenVM/model tests.
