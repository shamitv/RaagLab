# Phase 06 to-do

Updated: 2026-09-15. State: in_progress. The mock gate passed at `c7b2a87`;
normal-mode CPU verification and final certification remain open. Partial tasks
remain unchecked. See the [plan](plan.md) for concrete implementation gaps.

- [x] 06-01 Audit requirements and phase reports for the current checkpoint; correct unsupported completion claims and retain historical evidence.
- [ ] 06-02 Finish the dated official-source dependency support/fix review. Revision, lock hashes, image IDs/digests, runtime versions, and migration head are already recorded; rerun affected checks if pins change.
- [x] 06-03 Reproduce documented mock setup/start from an explicit committed revision with fresh configuration, isolated storage, and loopback networking.
- [ ] 06-04 Complete CPU/release runner corrections and executable regressions; pass normal-mode CPU inference in addition to the passing mock integration/recovery gate.
  - [ ] Align explicit CPU versus auto-fallback provenance and verify persisted deployment mode, auto GPU selection, and strict CUDA failure.
  - [ ] Apply 900-second warmup and 3,600-second inference budgets consistently to worker, verifier, and outer watchdogs.
  - [ ] Assert normal planning/token settings, no GPU allocation, exact lyrics, validated nontruncated audio, and matching download checksum.
  - [ ] Preserve timing fields and command logs; bound remaining subprocess/network calls and cover interruption/timeout behavior.
  - [ ] Provide at least 32 GiB available host RAM and the pinned read-only weights; current preflight is blocked.
- [ ] 06-05 Add and run real CPU browser playback/seek/download/refresh/reopen checks. Mock Chromium workflows and viewport/keyboard/reduced-motion/native-zoom inspection already ran; publish final-run attachments and record optional WebKit separately.
- [ ] 06-06 Verify CPU saved-state/audio preservation across the required lifecycle and finish cleanup ownership checks and failure reporting. Mock rebuild/update, stop/start, artifact dry-run, and Compose cleanup passed; final status must include worktree cleanup too.
- [x] 06-07 Refresh README, architecture, development, API, and model operating documentation for the current checkpoint.
- [x] 06-08 Publish the deployment handoff with service/storage/migration/routing/provider contracts and Part 2 ownership.
- [x] 06-09 Audit merged Part 2 D04/D05 reports within their recorded hardware, operations, and capability limits.
- [ ] 06-10 Finish evidence publication: individual A01–A12 and 06-AC mappings, final-run logs/screenshots, CPU measurements and acceptance, and the implemented/tested/blocked split. The mock summary and blocked preflight are published.
- [ ] 06-11 Certify the final committed candidate with `bash scripts/test.sh release --revision HEAD --real-cpu`, refresh exact tested commands, synchronize final reports, and close only after all required gates pass. Checkpoint tracking is updated.

No task has been removed or moved. See [status](status.md) and
[implementation report](implementation-status.md) for completed work and evidence.
