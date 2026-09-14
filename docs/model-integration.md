# Real model integration boundary

This document is the application handoff boundary for the selected YuE2 real
music provider. The portable application still defaults to the `mock` provider.
YuE2 is enabled only with the explicit real-worker Compose override and remains
subject to the Ubuntu1 queued-generation acceptance gate.

## Provider contract

The adapter must implement the existing `MusicProvider` interface in
`src/museforge/providers.py`: expose a stable provider ID and revision, declare
capabilities and readiness, normalize the effective generation request, and
produce a validated audio path through the existing progress and cancellation
callbacks. Initialization failures, unsupported controls, transient resource
failures, and cancellation must be typed provider outcomes. The adapter must not
return mock fixtures when model files, device access, or configuration are
missing.

For YuE2, the request mapping is explicit: `brief`, genre, mood, instruments and
tempo become the style prompt, and the persisted user-lyrics checkpoint becomes
the supplied lyric text. The application adapter sends full symbolic planning
and the accepted seed to the supervised YuE2 child. The current route accepts
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
PyTorch 2.10.0+cu128, CUDA 12.8 wheels, and `yue2-infer==0.1.5`. YuE2-3B and
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
and low prefetch. The worker performs a CUDA/BF16/weights/model warmup before
registering readiness. Keep the lease heartbeat responsive during planning,
synthesis, decoding and FLAC-to-WAV conversion. Cancellation must be cooperative
where the runtime supports it and bounded by the worker watchdog otherwise. On
timeout, OOM, cancellation, or worker loss, reap the child and preserve a typed
failure; do not publish an unvalidated or partial artifact.

Before finalization, decode the native FLAC, validate finite non-silent stereo
48 kHz audio, transcode it to 16-bit PCM WAV, and validate the published WAV
again before atomic publication. Persist provider ID, model/decoder revisions,
effective settings, seed, actual duration, and child validation metadata with the
version. The existing artifact publication and fenced job finalization remain
authoritative; mock artifacts continue to use exact-duration 44.1 kHz WAV.

## Required application verification

The standalone D03 evidence proves image-level CUDA/BF16 readiness and four
successful process-isolated outputs. Application integration remains open until
all of these pass:

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
revisions, CUDA/BF16, one GPU inference, and measured 900-second execution
limits. It does not start the mock worker and it never changes the default
`compose.yaml` mock profile.

Only then may D03 be marked completed. A standalone model command, image build,
or successful import cannot close the application real-model gate.
