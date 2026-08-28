Project name: StableRoster

Category: Intelligent Contracts

Batch: A

One-line description: Bilateral stable roster construction.

What it does: Consensus produces complete preference matrices for two cohorts; deterministic Gale-Shapley matching creates pairs that require member responses.

Why GenLayer: GenLayer consensus performs the bounded semantic step, then deterministic contract code executes and stores the mechanism-specific result.

Reusable: Yes. One deployment supports many independently keyed records and callers; the live fixture is only an example.

Repository: https://github.com/Leokings/stableroster (private; reviewers require read access).

Contract source: contracts/stable_roster.py

Source SHA-256: d71f28aedccee397f5eb30d69758d067b6887d9e075eb5a7aff4dbda8c58bf69

StudioNet contract: https://explorer-studio.genlayer.com/address/0x835D4992fc688AeAe043f0B30839BDB3132282D4

Deployment transaction: https://explorer-studio.genlayer.com/tx/0x9e0877fd5184a6acd93b8e8434a1658565e777bf887fa9b6364a99abf02e7f8d

Intelligent transaction: https://explorer-studio.genlayer.com/tx/0x4059545d610f6492dc06bf3f46bc8ccf0978c3358ddde766748c495bbc3627f4

Verification: GenVM lint PASS; strict typecheck PASS; 4 direct tests PASS; five-validator GLSim PASS; finalized StudioNet intelligent write and latest-final readback PASS; exact deployed-source and schema verification PASS.

Originality: Compared with 161 workspace contract sources. Nearest pre-existing structural score is 0.171086; mechanism and source hash are distinct.

Data boundary: Caller-supplied public data only. No external source fetching, funds, identity attestation, legal effect, or private-data guarantee.

Plain-text portal fields: SUBMISSION.txt. Notes / Description is within the 1,000-character form limit.
