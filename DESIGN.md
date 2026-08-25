# Design boundary

## Mechanism fingerprint

Consensus produces complete preference matrices for two cohorts; deterministic Gale-Shapley matching creates pairs that require member responses.

This is the contract's reusable mechanism, not a renamed domain wrapper.

## Consensus boundary

Validators independently re-execute the bounded semantic task and the custom validator rejects malformed or materially different output.

Every model response is normalized to an exact JSON shape, bounded list sizes,
closed indexes or bands, and deterministic ordering before it can affect state.
Inputs are explicitly framed as untrusted data rather than instructions.

## On-chain responsibilities

- validate bounded public inputs and isolate wallet roles;
- run the one semantic operation through GenLayer consensus;
- execute the mechanism-specific deterministic algorithm;
- persist independently keyed records and expose typed views;
- reject duplicate actions and invalid state transitions.

## Off-chain responsibilities

User interface, login, private drafts, source collection, provenance display,
notifications, analytics, and any real-world action remain off-chain.

## Non-goals

No payment, custody, identity attestation, legal ruling, physical verification,
professional advice, or guarantee that caller-supplied facts are true.
