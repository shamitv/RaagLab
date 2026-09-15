# Deployment handoff

Date: 2026-09-15. This handoff describes the portable Part 1 release and the
boundary to machine/model deployment. Phase 06 is complete on
`codex/phase-6-completion` at
`4b2d42599168925a4771dfc61901c4ad5456abd2`; its dated evidence package records
the mock release, normal CPU verification, browser correction, and dependency
review.

## Proven mock start

On a Linux Docker engine with Compose v2.24.4 or newer, from a clean checkout:

```bash
bash scripts/setup.sh
bash scripts/start.sh mock
bash scripts/migrate.sh
bash scripts/seed-demo.sh
bash scripts/smoke.sh mock
```

Open the loopback URL printed by `start.sh` (normally
`http://127.0.0.1:8000`). The API serves the compiled UI and API from one
origin. `bash scripts/stop.sh` stops containers while retaining the database,
broker, and artifact volumes. It does not reset user data. The release gate is
run with `bash scripts/test.sh release`; its dated evidence is under
`docs/implementation/evidence/06/`.

`bash scripts/test.sh release --revision HEAD --real-cpu` selects the normal-mode
CPU verifier. The target is explicit CPU, four threads, concurrency one, a 28 GiB
worker limit, 900-second warmup, and 3,600-second inference. The release runner
records durable provenance/audio checks, resource samples, separate timing,
bounded logs, ownership-checked cleanup, and stop/start checksums. The normal
CPU result and final browser correction are in the [Phase 06 completion
evidence](implementation/evidence/06/20260915-phase6-completion/README.md).
The expensive CPU command need not be repeated for routine operation; rerun it
when changing the model, decoder, lockfiles, or host prerequisites.

## Service and storage contract

The API, dispatcher, PostgreSQL database, RabbitMQ broker, and mock worker are
separate Compose services on the internal `backend` network. Only the API host
port is bound, and it is loopback-only. PostgreSQL is authoritative for jobs,
versions, settings, outbox messages, attempts, and idempotency. RabbitMQ carries
durable JSON dispatch envelopes; it is not a result store. The API mounts the
artifact volume read-only and the worker mounts it read/write.

Migrations run through `bash scripts/migrate.sh`, which invokes the guarded
Alembic runner and serializes concurrent upgrades. The current tested migration
head is `0004_worker_runtime` (following `0003_workspace_settings`). Artifact keys are
maintained with the read-only inspection command:

```bash
bash scripts/artifact-gc.sh
```

Deletion requires an explicit 24-hour-grace `--apply` invocation after review.
Backups, coordinated database/artifact snapshots, and verified restore are
deployment-phase responsibilities.

## Provider and capability boundary

The default `mock` provider is deterministic, produces validated non-silent
44.1 kHz stereo WAV, and is suitable for local operation without weights, GPU,
tokens, or paid services. It preserves submitted lyrics in the request and
version records, but its demo audio does not sing lyrics or semantically follow
musical controls.

The optional YuE2 route is selected by its separate Compose override and worker
image. `YUE2_DEVICE=cpu` omits GPU reservations; `YUE2_DEVICE=cuda` is strict
and requires the NVIDIA runtime; `auto` adds the GPU override only when the
Docker engine advertises an NVIDIA runtime, after which startup may select CPU
if its CUDA probe fails. Existing evidence proves a narrow English user-lyrics
route and technical 48 kHz audio retrieval/playback. It does not prove lyric adherence,
instrumental or vocal behavior, language fidelity, style fidelity, duration
control, or perceptual quality. Missing weights, devices, or model readiness
must fail explicitly; the application never silently falls back to mock audio.

## Part 2 ownership (D00–D05)

| Phase | Handoff responsibility |
| --- | --- |
| D00 inventory and plan | Record the target topology, hardware, OS/WSL and Docker versions, ports, storage locations, and model license/revision before changing the host. |
| D01 host preparation | Prepare layered device/toolkit readiness and resource limits; keep credentials, weights, and generated media outside the repository and image contexts. |
| D02 mock deployment | Re-run the documented mock command and API-served browser smoke on the target, including persistence and loopback/network checks. |
| D03 real model | Select the provider image/override, acquire and hash-lock model files, validate device readiness, route a real queued job, and retain provider provenance. |
| D04 system validation | Completed on Ubuntu1 with measured CUDA resources, one durable real job, cancellation, playback/range checks, and explicit capability gaps; repeat CPU and native-Linux checks as target resources permit. |
| D05 operations and handoff | Completed on Ubuntu1 with startup/update/rollback, coordinated database/artifact backup, isolated restore playback, bounded drain, and portability records. |

Part 2 must preserve the API/database/broker/artifact/routing contracts above.
Host-specific paths, devices, model caches, and resource limits belong in its
deployment configuration and must not be copied into the portable mock setup.

## Troubleshooting

- `setup.sh` requires a reachable Linux Docker engine and Compose plugin; it
  preserves an existing `.env` even when prerequisite checks fail.
- A queued job with an unavailable worker remains durable and is recovered when
  the selected worker returns. Inspect readiness with `/health/ready` and use
  `bash scripts/logs.sh` for correlated, redacted service logs.
- A missing or unsafe artifact returns an explicit unavailable response; it is
  never replaced by generated media.
- A real-provider request must use the matching worker route and revision. An
  absent model/device is a startup or typed provider failure, not a mock success.
