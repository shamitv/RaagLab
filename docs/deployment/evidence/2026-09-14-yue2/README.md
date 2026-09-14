# YuE2-3B standalone test — 2026-09-14

The pinned YuE2-3B image successfully generated all three requested songs on the
local RTX 5080 laptop GPU. A fresh offline container repeated the first prompt
with identical FLAC and decoded-PCM hashes. All four attempts passed the defined
technical audio checks and released GPU memory. Listening quality and lyric
adherence remain **pending**: no listening tool was available in this session.

This is a standalone batch deployment. No application API, database, Celery
worker, or frontend integration changed. This result does not complete the
application's Phase 5 provider-readiness work. Earlier verification evidence is
preserved unchanged.

## Actual results

| Prompt / seed | Audio duration | Process wall time | Peak whole-device GPU use | Result |
| --- | ---: | ---: | ---: | --- |
| Acoustic folk / 42 | 99.00 s | 58.97 s | 9197 MiB | Passed |
| Upbeat synth-pop / 43 | 42.08 s | 33.64 s | 9057 MiB | Passed |
| Piano ballad / 44 | 82.04 s | 49.28 s | 9161 MiB | Passed |
| Folk repeat / 42, fresh container | 99.00 s | 57.34 s | 9197 MiB | Passed; identical audio |

Every output is decodable 48 kHz stereo FLAC with finite samples and natural
token completion. None reached the planning or semantic token limit. All outputs
passed the non-silence and near-clipping screening thresholds documented in the
test runbook. Synth-pop contained three samples at absolute amplitude >= 0.999
(0.0000743% of samples), below the 1% rejection threshold; the other clips had
none. This is not a listening assessment of distortion or musical quality.

Each attempt used CUDA, BF16 AR/NAR, FP32 VAE, full symbolic planning, default
sampling limits, no quantization, and no AR offloading. The official runtime
reported CUDA graph execution with flash attention. No CUDA OOM retry was needed.
The 900-second generation deadline was never reached. GPU use returned to
637,480,960 bytes at each supervisor recovery check; a later external observation
showed 308 MiB. Whole-device readings include display/driver memory and may vary.

Peak process-tree RSS was 9.18–9.33 GiB. Available WSL host memory remained above
21.15 GiB during the sampled generation attempts. PyTorch's per-attempt peaks,
whole-device readings, raw/decoded audio statistics, and file hashes are retained
in the two run reports. The process timings include interpreter startup,
verification, model loading, inference, artifact writing, and shutdown. Each
attempt loads the model in a new process; these are not persistent-worker warm
throughput measurements. Stage-level timings are in `stage-timings.json`.

## Reproduction and runtime

See [the container runbook](../../../../packaging/yue2/README.md) for build,
acquisition, test, and restart commands. Exact original lyrics and style prompts
are committed in [prompts.json](../../../../packaging/yue2/prompts.json).

- Tested code commit: `c5400a2` on `model_deploy`.
- Local image: `musicgen-yue2:0.1.5`, 12,028,725,411 bytes.
- Image ID: `sha256:625a4cc64bc869b1d6b0a642d2803b5ab5939bfcc513b6d95468bb1968b000ac`.
- Python 3.12.14; PyTorch 2.10.0+cu128; official `yue2-infer` 0.1.5.
- Ubuntu1 / WSL2 kernel 6.6.87.2; Docker 29.8.0; Compose 5.5.1.
- NVIDIA Container Toolkit 1.19.0; Windows driver 592.01.
- RTX 5080 Laptop GPU, 16,303 MiB; WSL RAM 31.06 GiB.
- YuE2-3B revision `29b3558dd46954a0cd9021dc76d5c91864a0f1c7`.
- YuE2-Vae revision `9a94e1d0ea9f8087e98f77fa88df4a4068104d2a`.

Upstream recommends a 24 GB GPU. This evidence establishes successful execution
of these short-lyrics cases on this particular 16 GB device; it does not establish
maximum-context or concurrent-generation support. Both models use CC BY-NC 4.0
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

Full generated audio, scores, tokens, latents, inputs, settings and logs are
retained in Docker volume `musicgen-yue2-test_outputs`. Verified weights remain
in `musicgen-yue2-test_weights`. A 61,463,344-byte copy of results is available at
`C:/work/musicgen/.local/yue2-results`, ignored by Git. Machine-readable reports
and verification logs are committed here; generated media/arrays remain outside
Git.

## Local playback

- [Acoustic folk](C:/work/musicgen/.local/yue2-results/20260914T024054027064Z-batch/acoustic-folk-baseline/audio.flac)
- [Upbeat synth-pop](C:/work/musicgen/.local/yue2-results/20260914T024054027064Z-batch/synth-pop-baseline/audio.flac)
- [Piano ballad](C:/work/musicgen/.local/yue2-results/20260914T024054027064Z-batch/piano-ballad-baseline/audio.flac)
- [Folk restart repeat](C:/work/musicgen/.local/yue2-results/20260914T024340479084Z-restart/acoustic-folk-baseline/audio.flac)

These links target this machine's exported files. Listening for style, intelligible
lyrics, phrasing, structure, and audible defects remains the outstanding manual
acceptance step; technical validity alone does not establish those properties.
