# Part 2 deployment status

- State: `completed`
- Last updated: 2026-09-15
- Verification target: reference Ubuntu/WSL2 deployment with a Linux Docker Engine
- Current focus: dated handoff complete; live deployment state is recorded locally

## Completed

- D00 target inventory, topology, model decision, phase plan, and acceptance rules.
- D01 Docker/Compose and GPU readiness on the reference host class.
- D02 target mock gate: 49 integration checks, 34 browser checks, and 22 intentional skips;
  queued restart, broker/dispatcher restart, worker-loss recovery, and full restart passed.
- D03 integrated YuE2 adapter, isolated worker image/queue, startup readiness, provenance,
  and no-fallback behavior.
- D04 persistent real verification: one durable queued YuE2 job, CUDA provenance, persisted
  48 kHz stereo audio, retrieval/hash/range checks, and 77.2387-second measured output for
  an 8-second request. Queued cancellation also passed.
- D05 integrated runbook, manifest, private environment generation, isolated Compose project,
  bounded drain, logical backup/restore, isolated playback, update/rollback, and portability record.

## Remaining work

- None for the recorded D04/D05 acceptance gates. Native Linux remains documented only.

## Limitations

Exact-lyrics adherence, vocal/language breadth, style controls, instrumental fidelity, exact
duration, subjective listening quality, and native-Linux execution remain unverified.

## Latest verification

See [D04/D05 evidence](evidence/2026-09-15-d04-d05/README.md), the integrated D03 evidence,
and the managed runbook and reference manifest. The D05 backup/restore and rollback checks
have dated evidence; live health belongs in ignored local documentation. The remaining
native-Linux and semantic-audio limitations are explicitly recorded.
