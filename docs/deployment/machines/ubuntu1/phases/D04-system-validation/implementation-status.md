# D04 implementation status

D04 completed on Ubuntu1 on 2026-09-15. The persistent project
`museforge-ubuntu1` ran the API, dispatcher, and one GPU YuE2 worker with the
existing verified weights volume.

- Real readiness reached `ready` with CUDA, BF16, pinned model and decoder revisions.
- One request passed the API, PostgreSQL/outbox, RabbitMQ route
  `museforge.yue2.v1`, worker, persisted version/artifact, and API retrieval.
- WAV metadata, full GET, HEAD, and byte-range retrieval checks passed.
- Requested lyrics were preserved; measured output was 77.2387 seconds for an
  8-second request.
- Worker cold initialization completed in about 5.9 seconds in the readiness log;
  the real adapter reported CUDA/BF16 and one active inference. The D03 runtime
  record measured 8.44 GiB torch peak allocation and 8.69 GiB reserved allocation;
  the standalone target run measured about 9.1 GiB whole-device peak use. These
  are bounded observations, not throughput guarantees.
- Queued cancellation passed after stopping and restarting only the deployment worker.
- Repeatable broker, dispatcher, worker-loss, and full restart evidence is labelled
  mock-provider evidence from the isolated D02 run.

Evidence is under the private host path
`/home/shamit/.local/share/museforge-ubuntu1/evidence/20260915T030821Z-real`.
Musical quality, lyric adherence, broader language/vocal behavior, exact duration,
and native Linux remain unverified.
