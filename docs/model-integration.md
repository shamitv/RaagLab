# Real model integration boundary

This document is the application handoff boundary for the selected YuE2 real
music provider. The portable application still defaults to the `mock` provider.
YuE2 is enabled only with the explicit real-worker Compose override and remains
validated by the Ubuntu1 queued-generation acceptance gate on 2026-09-14. See
[application evidence](deployment/evidence/2026-09-14-d03-review-corrections/README.md).

## Provider contract

The adapter must implement the existing `MusicProvider` interface in
`src/museforge/providers.py`: expose a stable provider ID and revision, declare
capabilities and readiness, normalize the effective generation request, and
produce a validated audio path through the existing progress and cancellation
callbacks. Initialization failures, unsupported controls, transient resource
failures, and cancellation must be typed provider outcomes. The adapter must not
return mock fixtures when model files, device access, or configuration are
missing.

## Capability audit

Capability state is evidence-backed: `supported` means the behavior was verified,
`unsupported` means the active adapter does not provide it, and `unknown` means the
request may be accepted but the output behavior has not been demonstrated. The
capability matrix is returned by `/api/v1/capabilities` and copied into new version
provenance. Legacy boolean fields are `null` when behavior is unknown.

| Capability | CPU mock | YuE2 `yue2-infer-0.1.6` | Evidence and limits |
| --- | --- | --- | --- |
| Supplied lyrics text | Supported | Supported | API preserves user text; YuE2 route accepts English user lyrics. This does not prove singing. |
| Separate lyrics generation | Supported as scripted demo text | Unsupported | Mock text is deterministic scripted content, not an LLM result; YuE2 consumes supplied lyrics. |
| Instrumental music generation | Unsupported | Unknown | Mock tones are not semantically conditioned music. YuE2 accepts an Instrumental request but may include vocals. |
| Vocal generation | Unsupported | Unknown | Vocal presence and behavior have not been audited for YuE2. |
| Exact supplied lyrics sung | Unsupported | Unknown | Lyrics reach YuE2, but adherence was not measured. |
| Audio language fidelity | Unsupported | Unknown | The app route was exercised with English lyrics only; language fidelity was not measured. |
| Instrument, mood, genre, tempo fidelity | Unsupported | Unknown | Mock ignores these controls. YuE2 receives them in its style prompt; output fidelity has not been evaluated per control. |
| Requested duration control | Supported | Unsupported | Mock audio matches the requested seconds. YuE2 duration is model-determined and may exceed the request. |
| Seed reproducibility | Supported | Unknown | Mock PCM is deterministic; the seed reaches YuE2, but cross-runtime reproducibility is unverified. |
| Audio conditioning, editing, continuation | Unsupported | Unsupported | No active route accepts reference audio, edits an artifact, or continues from one. |
| Technical audio output | Supported | Supported | Mock emits validated 44.1 kHz stereo WAV. The D03 queued YuE2 result was a verified 48 kHz stereo PCM WAV retrievable through the API. This is format evidence, not semantic music-quality evidence. |

The real route currently allows only `generate`, English, and user-supplied lyrics.
Refinement, variation, regeneration, lyrics-only editing, non-English requests,
and duration control remain unavailable or unverified; the UI must not present
them as active behavior. The request's `Instrumental` value is retained for
contract compatibility and is explicitly not a guarantee about YuE2 output.

For YuE2, the request mapping is explicit: `brief`, genre, mood, instruments and
tempo become the style prompt, and the persisted user-lyrics checkpoint becomes
the supplied lyric text. The application adapter sends full symbolic planning
and the accepted seed to the supervised YuE2 child (except the explicitly marked
32-token integration smoke mode described in [development](development.md#yue2-cuda-first--cpu-fallback)). The current route accepts
English user lyrics and the existing `Instrumental` request shape as a narrow
compatibility path. The output may contain vocals; the application makes no
claim about exact lyric adherence, vocal behavior, language coverage, or
requested duration.

## Image and dependency isolation

Keep the real worker in a separate image and dependency group. API, dispatcher,
database, broker, and CPU mock images remain free of the YuE2/PyTorch CUDA stack.
The integrated worker uses the separate hash-locked
`packaging/yue2/requirements.museforge.lock` for its Python 3.12 application
runtime; CUDA, PyTorch, and YuE2 remain confined to the YuE2 lock.
The current reference image is `packaging/yue2/Dockerfile` with Python 3.12,
PyTorch 2.10.0+cu128, CUDA 12.8 wheels, and hash-verified official
`yue2-infer==0.1.6` source at `0edaf2f4053ef4731334b8329834b107977f9637`. YuE2-3B and
YuE2-Vae revisions, hashes, license, and acquisition rules are in
`packaging/yue2/model-lock.json` and `acquire.py`.

Weights and generated media stay in persistent volumes outside Git and image
layers. Acquisition is separate from startup, uses immutable revisions, checks
available disk, verifies Hub metadata/file hashes, and supports reusing a valid
download. Tokens must never appear in image history, logs, committed manifests,
or frontend bundles.

## Queue and lifecycle

Give the real provider its own queue and worker route. The implemented route is
`museforge.yue2.v1`; `MUSIC_PROVIDER=yue2` selects it while `mock` remains the
default. The worker must reject an
envelope for another route or provider revision, and a mock worker must never
consume a real request. Readiness becomes `ready` only after the selected image,
weights, device, and model initialization succeed. The API remains live while the
real worker warms up.

Load the model in a supervised inference child, with one active request per GPU
and low prefetch (one request per CPU worker too). The worker verifies weights,
resolves `DEVICE=auto` to CUDA with BF16 or CPU, and loads the model before
registering readiness. Keep the lease heartbeat responsive during planning,
synthesis, decoding and FLAC-to-WAV conversion. Cancellation must be cooperative
where the runtime supports it and bounded by the worker watchdog otherwise. On
timeout, OOM, cancellation, or worker loss, reap the child and preserve a typed
failure; do not publish an unvalidated or partial artifact in production.
Only startup device-probe failures allow CPU fallback; job errors never switch
devices. Smoke-test artifacts are deliberately tiny/truncated and marked in
the accepted snapshot and provenance, never substituted for production output.

Before finalization, decode the native FLAC, validate finite non-silent stereo
48 kHz audio, transcode it to 16-bit PCM WAV, and validate the published WAV
again before atomic publication. Persist provider ID, model/decoder revisions,
effective settings, seed, actual duration, and child validation metadata with the
version. The existing artifact publication and fenced job finalization remain
authoritative; mock artifacts continue to use exact-duration 44.1 kHz WAV.

## Integrated route regression checks

The standalone D03 evidence proves image-level CUDA/BF16 readiness and successful
process-isolated outputs. The integrated worker also passed its application gate
on 2026-09-14. Keep these checks in regression coverage:

1. A real request is accepted by the API and published through the durable outbox
   and real queue.
2. The real worker claims it, reports readiness/progress, and writes a provider-
   and model-specific provenance snapshot.
3. The persisted result is retrieved through the API and plays/seeks in the
   API-served browser.
4. Mock and real routes, missing model/device, unsupported controls, cancellation,
   worker loss, restart, and retry behavior have focused tests.

## Enabling the real worker

Build the integrated worker from the repository root with
`packaging/yue2/Dockerfile.worker`, after the standalone model volume
`musicgen-yue2-test_weights` has been acquired and verified. Start the API,
dispatcher, and the `yue2` Compose profile with `compose.yue2.yaml`. The override
sets `MUSIC_PROVIDER=yue2`, `LYRICS_PROVIDER=user`, the pinned model and decoder
revisions, auto device selection/BF16, one inference process, and 900-second execution
limits. It does not start the mock worker and it never changes the default
`compose.yaml` mock profile.

The base YuE2 override has no mandatory GPU reservation. Add
`compose.yue2.gpu.yaml` for GPU exposure on a configured NVIDIA host. CPU-only
VM integration uses `bash scripts/test.sh yue2-cpu`, which explicitly enables
short smoke mode in a disposable stack; production smoke mode remains disabled.

The Phase 6 release gate runs the pinned model in normal mode on CPU:

```bash
bash scripts/test.sh release --real-cpu
```

That gate requires 32 GiB available host memory, a 28 GiB worker limit, four
CPU threads, one active job, and the external verified weights volume. It checks
normal planning, nontruncated validated audio, CPU/`torch-eager` provenance,
durable persistence, API playback/range/hash retrieval, and sampled resources.
It does not establish lyric adherence, musical quality, or exact duration.

D03 closure is supported by the recorded durable application result, not merely
a standalone model command, image build, or successful import. Broader provider
semantics and quality remain outside this narrow verification.

Part 1 release verification covers the mock provider and, when requested, the
normal CPU YuE2 gate. The release gate does not widen any YuE2 semantic quality
claim. See the [deployment handoff](deployment-handoff.md) and [Phase 06
evidence](implementation/evidence/06/20260915-phase6-completion/README.md).
