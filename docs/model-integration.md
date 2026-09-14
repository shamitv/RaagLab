# Real model integration boundary

This document is the application handoff boundary for a future real music
provider. The portable application currently runs the `mock` provider. The
standalone YuE2-3B image and its Ubuntu1 evidence are a Part 2 D03 checkpoint;
they are not an adapter or an active application route.

## Provider contract

The adapter must implement the existing `MusicProvider` interface in
`src/museforge/providers.py`: expose a stable provider ID and revision, declare
capabilities and readiness, normalize the effective generation request, and
produce a validated audio path through the existing progress and cancellation
callbacks. Initialization failures, unsupported controls, transient resource
failures, and cancellation must be typed provider outcomes. The adapter must not
return mock fixtures when model files, device access, or configuration are
missing.

For YuE2, the request mapping is explicit: `brief` and supported style fields
become the style prompt, and user lyrics become the supplied lyric text. The
current standalone fixture uses English lyrics, full symbolic planning, seeds
42–44, and model-determined durations. It proves neither exact sung-lyric
accuracy nor every product language, vocal, continuation, editing, or iteration
control. The API/UI must expose only capabilities verified for the selected
revision and mark the rest unsupported or pending.

## Image and dependency isolation

Keep the real worker in a separate image and dependency group. API, dispatcher,
database, broker, and CPU mock images remain free of the YuE2/PyTorch CUDA stack.
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

Give the real provider its own queue and worker route. The worker must reject an
envelope for another route or provider revision, and a mock worker must never
consume a real request. Readiness becomes `ready` only after the selected image,
weights, device, and model initialization succeed. The API remains live while the
real worker warms up.

Load the model in the inference child, with one active request per GPU and low
prefetch. Keep the lease heartbeat responsive during planning, synthesis, and
decoding. Cancellation must be cooperative where the runtime supports it and
bounded by the worker watchdog otherwise. On timeout, OOM, cancellation, or
worker loss, reap the child and preserve a typed failure; do not publish an
unvalidated or partial artifact.

Before finalization, validate decodability, non-empty duration, sample rate,
channels, finite samples, content type, and checksum. Persist provider ID,
model/revision, effective settings, seed, actual duration, and measured resource
metadata with the version. The existing artifact publication and fenced job
finalization remain authoritative.

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

Only then may D03 be marked completed. A standalone model command, image build,
or successful import cannot close the application real-model gate.
