# YuE2-3B standalone test — 2026-09-14

The pinned YuE2-3B image successfully generated all three requested songs on a
compatible NVIDIA GPU. A fresh offline container repeated the first prompt
with identical FLAC and decoded-PCM hashes. All four attempts passed the defined
technical audio checks and released GPU memory. Listening quality and lyric
adherence remain **pending**: no listening tool was available in this session.

This is a standalone batch deployment. No application API, database, Celery
worker, or frontend integration changed. This result does not complete the
application's Phase 5 provider-readiness work. Unsanitized machine evidence is
preserved only in the ignored local originals; tracked evidence retains the
verification outcome without host identifiers.

## Actual results

| Prompt / seed | Audio duration | Result |
| --- | ---: | --- |
| Acoustic folk / 42 | 99.00 s | Passed |
| Upbeat synth-pop / 43 | 42.08 s | Passed |
| Piano ballad / 44 | 82.04 s | Passed |
| Folk repeat / 42, fresh container | 99.00 s | Passed; identical audio |

Every output is decodable 48 kHz stereo FLAC with finite samples and natural
token completion. None reached the planning or semantic token limit. All outputs
passed the non-silence and near-clipping screening thresholds documented in the
test runbook. Synth-pop contained three samples at absolute amplitude >= 0.999
(0.0000743% of samples), below the 1% rejection threshold; the other clips had
none. This is not a listening assessment of distortion or musical quality.

Each attempt used CUDA, BF16 AR/NAR, FP32 VAE, full symbolic planning, default
sampling limits, no quantization, and no AR offloading. The official runtime
reported CUDA graph execution with flash attention. No CUDA OOM retry was needed.
The 900-second generation deadline was never reached, and device memory recovered
after every attempt. Exact host resource measurements and inventory values are
retained in the ignored local originals. Audio statistics and hashes remain in
the tracked reports. Each attempt loads the model in a new process, so these are
not persistent-worker warm-throughput measurements.

## Reproduction and runtime

See [the container runbook](../../../../packaging/yue2/README.md) for build,
acquisition, test, and restart commands. Exact original lyrics and style prompts
are committed in [prompts.json](../../../../packaging/yue2/prompts.json).

- Tested code commit: `c5400a2` on `model_deploy`.
- Local image: pinned standalone YuE2 validation image.
- Python 3.12.14; PyTorch 2.10.0+cu128; official `yue2-infer` 0.1.5.
- Reference platform: Ubuntu/WSL2 with a compatible Linux Docker and NVIDIA stack.
- YuE2-3B revision `29b3558dd46954a0cd9021dc76d5c91864a0f1c7`.
- YuE2-Vae revision `9a94e1d0ea9f8087e98f77fa88df4a4068104d2a`.

The reference host did not meet every upstream hardware recommendation. This
evidence establishes successful execution of these short-lyrics cases but does
not establish maximum-context or concurrent-generation support. Both models use CC BY-NC 4.0
weights. [Official model card](https://huggingface.co/m-a-p/YuE2-3B).

## Verification evidence

- Hash-locked image build and `pip check`: passed. Initial image built on
  September 13; song acceptance runs executed September 14 at approximately
  02:40–02:44 UTC (08:10–08:14 Asia/Calcutta).
- CUDA availability, BF16, capability 12.0, and GPU matrix operation: passed.
- Both immutable model snapshots: all 21 selected runtime/notice files verified
  against Hub Git/LFS hashes; verified again offline before each batch.
- Linux Bash syntax and Compose configuration validation: passed.
- Nine harness tests: passed in 6.475 seconds, covering valid FLAC, silence,
  clipping, nonfinite samples, wrong format/duration, success/failure exits,
  deadline cleanup/recovery, and SIGKILL of a process ignoring SIGTERM.
- Three-prompt batch: exit 0, three successful baseline attempts.
- Fresh-container restart: exit 0; same model cache and no network access;
  FLAC and PCM hashes both identical to the first folk run.
- GPU memory recovery: passed after all four attempts. No test containers remain
  running, and no image was published. No application suite rerun was needed for
  this isolated packaging-only change.

Full generated audio, scores, tokens, latents, inputs, settings, and logs remain
outside Git in the configured output volume. Verified weights remain in the
configured external weights volume. Exact local locations are recorded only in
ignored machine documentation; sanitized machine-readable reports and
verification logs are committed here.

## Local playback

Generated-media locations are intentionally not linked from tracked documents.
Listening for style, intelligible lyrics, phrasing, structure, and audible
defects remains the outstanding manual
acceptance step; technical validity alone does not establish those properties.
