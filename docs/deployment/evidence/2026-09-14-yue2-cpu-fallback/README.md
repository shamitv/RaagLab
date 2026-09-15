# YuE2 startup fallback and short queued audio

Verified on the reference host with Linux Docker Engine 29.8.0 / Compose v5.5.1.
Runtime: official YuE2 0.1.6 source at
`0edaf2f4053ef4731334b8329834b107977f9637`, PyTorch 2.10.0+cu128,
Python 3.12. The source archive SHA-256 and independently pinned model/decoder
revisions are in `packaging/yue2/model-lock.json`; dependencies and build tools
are hash-locked. Weights were reused from the verified, read-only external
`museforge-yue2-weights` volume. No mock inference or network was used by
the inference children.

## Real service checks

`python3 scripts/verify-yue2-devices.py` created the disposable project
`<isolated-cpu-project>` with no GPU reservation. `DEVICE=auto`
selected CPU, `torch-eager`, and `fallback_reason=cuda_unavailable`.
Four CPU threads and a 28 GiB container memory limit were configured.

The CUDA variant (`--gpu`) created `<isolated-gpu-project>` with the
optional GPU override, selected CUDA/`torch`, and reported no fallback reason.
The GPU host was the existing compatible NVIDIA GPU. This confirms the CUDA-first
path remains available, not cross-device determinism.

Both used the real PostgreSQL/RabbitMQ/API/dispatcher/Celery prefork worker,
one published outbox envelope, one attempt, one durable version, exact persisted
user lyrics, startup-selected device in the worker registration, and matching
runtime provenance. API artifact GET/HEAD/range and SHA-256 verification passed.
Each output was 61,376 stereo frames at 48 kHz (1.2786667 seconds), finite,
nonzero, transcoded from native FLAC to published 16-bit PCM WAV.

CPU adapter elapsed time was 32.57 seconds (30.44 inside inference); CUDA was
17.99 seconds (15.55 inside inference). These are single short-sample timings,
not performance guarantees. Generated WAVs, jobs, readiness, provenance, and
service logs remain in ignored `test-results/yue2-devices/<project>/`.
Only the generated projects' containers/database/broker/artifact volumes were
removed; external weights and the existing application stack were preserved.

The initial CPU acceptance attempt ended early because the harness treated
container health as completed model warmup. The harness now waits separately
for provider readiness; that failed attempt's log is retained under project
`<isolated-test-project>`.

## Supporting regression checks

The full existing real-service mock regression suite passed all 48 tests,
including migrations, routing, job lifecycle, recovery, and publication.
The final local unit suite passed all 158 tests, including CPU/CUDA OOM
classification and no per-job fallback. A focused run passed 13
migration/provider-routing tests, including saved
smoke-mode compatibility and CPU readiness metadata. The frontend typecheck,
production build, and three unit tests passed with regenerated API types.
Offline startup checks passed for explicit CPU and strict CUDA without GPU,
missing weights, conflicting identity, and warmup timeout (failures did not
resolve auto or report readiness).

## Scope

Smoke mode was explicitly enabled across each isolated stack, frozen in the
accepted snapshot, and marked in provenance. It skips symbolic planning,
generates exactly 32 greedy semantic tokens, and uses the default 32 synthesis
steps. Semantic truncation is expected and permitted only in smoke mode.
Production smoke mode remains off; full planning, normal token limits, and
original >5-second/nontruncated validation remain unchanged.

The CPU test ran on a GPU-equipped WSL host with no GPU exposed to its worker,
not on a separately provisioned GPU-free VM. The base Compose stack has no
NVIDIA reservation/toolkit dependency and can use the same test on a VM with
verified weights and sufficient RAM. Full-song CPU latency, audio quality,
lyric adherence, and browser perceptual playback are not certified by this test.
