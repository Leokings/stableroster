# Source policy

StableRoster does not fetch websites, APIs, files, or private databases.
It evaluates only bounded public calldata supplied by a caller. Therefore:

- the contract never implies that a URL or real-world claim was independently verified;
- source selection, provenance, licensing, and freshness remain client responsibilities;
- validators receive the same stored public snapshot and closed policy;
- prompt text labels all caller material as untrusted data, never instructions;
- results are reusable semantic/algorithmic outputs, not factual attestations.

If a deployment needs live-world evidence, an off-chain client must collect and
display that evidence before calling the contract. Adding external fetching would
change the trust model and requires a new audit and StudioNet deployment.
