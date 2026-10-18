# Review checklist — current v2, 2026-10-18

- [x] Strict leader-index validation blocks Boolean/float equality spoofing
- [x] Maximum seven-day deadline, exact-boundary guard and permissionless expiry
- [x] Unique nonzero participant wallets and immutable terminal states
- [x] Pinned runner; local GenVM lint and strict typecheck pass
- [x] 25 direct contract tests, including forged leaders and 2x2 stability profiles
- [x] 4 local five-validator lifecycle cases: SEALED/DECLINED/WITHDRAWN/EXPIRED
- [x] 11 offline journal tests, including pending resume and uncertain broadcast
- [x] Breaking API/schema change and public-profile trust boundary documented
- [x] Historical v1 proof separated; its live state was AWAITING_RESPONSES only
- [x] Scoped comparison against 22 prior submissions and EvidenceCircuit
- [ ] Verify current network/client/runner with an approved probe
- [ ] Push reviewed source after owner approval
- [ ] Fresh repository-specific wallets and approved v2 deployment
- [ ] Real-model complete bilateral acceptance, decline and withdrawal flows
- [ ] Finalized unauthorized/replay/terminal-state expected failures
- [ ] Real-time deadline/permissionless-expiry test and profile-injection cases
- [ ] Final-state readbacks and exact deployed source/schema verification
- [ ] Public manifest with commit, blob, all receipts, votes and expected failures
- [ ] Public repo only with explicit permission; evidence links checked logged out
- [ ] Replace draft fields, then owner submits through the Portal

Local five-validator mocks are not live heterogeneous-model or GenVM proof.
No visibility change, push, deployment or Portal action was performed here.
