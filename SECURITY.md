# Security

## Protected assets

Record integrity, role separation, bounded execution, deterministic algorithm
results, and exact deployed-source provenance.

## Controls

- concrete GenVM runner and Python tool versions are pinned;
- keys, list sizes, numeric bands, text lengths, ASCII boundaries, and JSON shapes are bounded;
- model output is normalized before storage;
- a custom validator independently checks every nondeterministic call;
- write roles are checked against `gl.message.sender_address`;
- duplicate records and duplicate role actions are rejected;
- the live proof reads finalized state and exact deployed source;
- wallet secrets remain in ACL-restricted files outside the workspace.

## Public-data warning

All calldata and stored content are public. Do not submit secrets, personal data,
private documents, or confidential source material.

## Excluded guarantees

This contract does not move funds and does not authenticate real-world identity,
ownership, authority, evidence provenance, or legal consequences. Report a
suspected issue privately before public disclosure.
