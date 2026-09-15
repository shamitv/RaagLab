# Ubuntu1 D04/D05 deployment evidence

Date: 2026-09-15. Host: Ubuntu 24.04.5 in WSL2, Docker Engine 29.8.0, Compose
5.5.1, RTX 5080 Laptop GPU with 16,303 MiB VRAM. Project: `museforge-ubuntu1`.

## D02 target mock gate

The disposable target project `museforge-phase4-test-7376f5f707c2` passed 49
integration checks and 34 browser checks, with 22 intentional skips. Evidence
included API-served generation, playback/seek/download, version iteration and
reopen, queued restart, broker recovery, dispatcher restart, worker loss, full
restart, and service logs. The project was isolated from the persistent stack and
cleaned up after the run.

## D04 integrated real gate

The persistent project ran the API, dispatcher, and one `worker-yue2` container;
the old mock worker was stopped. `scripts/deploy/verify.sh real` produced a
successful durable job with one attempt, model `m-a-p/YuE2-3B`, revision
`29b3558dd46954a0cd9021dc76d5c91864a0f1c7`, decoder revision
`9a94e1d0ea9f8087e98f77fa88df4a4068104d2a`, CUDA runtime, 48 kHz stereo WAV,
full GET/HEAD/byte-range retrieval, and a measured duration of 77.2387 seconds
for an 8-second request. The private JSON/WAV evidence is under
`/home/shamit/.local/share/museforge-ubuntu1/evidence/20260915T030821Z-real`.

The real queued cancellation checkpoint is implemented in
`scripts/deploy/recovery.sh`; broader repeatable broker, dispatcher, worker-loss,
and restart fault checks remain labelled mock evidence. No listening tool was
available, so musical quality and lyric adherence remain unverified.

## D05 state

The integrated runbook and manifest describe the persistent project, private
credentials, separate volumes, model pin, WSL recovery, drain, logical PostgreSQL
backup, artifact archive, isolated restore, update, and rollback guardrails. The
backup, isolated restore/playback, update, and rollback restore gates passed. The
primary project was restarted after the checks and remains healthy on port 8000.
