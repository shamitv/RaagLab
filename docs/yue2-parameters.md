# YuE2 parameters and MuseForge mapping

This reference describes the pinned YuE2 runtime used by MuseForge and separates
what the model runtime accepts from what the MuseForge product currently exposes.
It is based on the installed `yue2-infer==0.1.6` API, the pinned model files, and
the official YuE2 documentation and examples listed under [Sources](#sources).

## Pinned runtime

| Component | Pinned value | Role |
| --- | --- | --- |
| Model | `m-a-p/YuE2-3B` at `29b3558dd46954a0cd9021dc76d5c91864a0f1c7` | Plans and generates a song from style and lyrics. |
| Decoder | `m-a-p/YuE2-Vae` at `9a94e1d0ea9f8087e98f77fa88df4a4068104d2a` | Decodes acoustic latents into listening audio. |
| Inference package | `yue2-infer==0.1.6` from YuE revision `0edaf2f4053ef4731334b8329834b107977f9637` | Provides `YuE2Pipeline`. |
| Output | 48 kHz stereo FLAC from YuE2; MuseForge publishes validated 16-bit PCM WAV | The native and application publication formats differ. |
| Recommended accelerator | BF16-capable NVIDIA GPU; one request at a time | Upstream starts at 24 GB VRAM. MuseForge can use its separately verified CPU fallback. |

The model weights use CC BY-NC 4.0. The runtime source uses Apache 2.0. The
repository lock in `packaging/yue2/model-lock.json` is authoritative for a
MuseForge deployment.

## MuseForge inputs

The browser and `POST /api/v1/generations` use the following product-level
parameters. The API contract is intentionally narrower than the underlying
model API.

| Parameter | Type and accepted value | Default | YuE2 mapping and current status |
| --- | --- | --- | --- |
| `brief` | String, 1–500 characters | Required | Appended to the YuE2 `style` string. |
| `instruments` | One or more of Guitar, Piano, Tabla, Drums, Bass, Strings, Synth | Required | Joined into the `style` string. This influences prompting; adherence is unmeasured. |
| `mood` | Happy, Melancholic, Romantic, Energetic, Calm, Epic | Required | Lowercased and added to `style`; adherence is unmeasured. |
| `language` | Product schema: Hindi, English, Hinglish, Punjabi, Tamil | English | The YuE2 route currently accepts only English. Other values receive `unsupported_capability`. |
| `genre` | Indie Pop, Pop, Folk, Ambient, Rock, Electronic | Indie Pop | Lowercased and added to `style`; adherence is unmeasured. |
| `tempo` | Slow, Medium, Fast | Medium | Lowercased and added to `style`; it is descriptive rather than an exact BPM control. |
| `vocal_type` | `Instrumental` | Instrumental | Retained for API compatibility and added to `style`. It does not guarantee an instrumental result; YuE2 may generate vocals. |
| `lyrics.mode` | `user` for the YuE2 route | Configured provider | YuE2 requires non-empty user-supplied lyrics. It does not write lyrics for MuseForge. |
| `lyrics.text` | Unicode string, at most 20,000 characters and 80,000 UTF-8 bytes | Required for YuE2 | Passed intact to YuE2 `lyrics`. Section tags and stanza breaks are recommended. |
| `duration_seconds` | Integer, 5–30 | 8 | Persisted as requested intent. YuE2 does not use it to set output length. |
| `seed` | Unsigned 32-bit integer | Randomly assigned once | Passed to YuE2. Identical seeds are not guaranteed to reproduce output across runtime, device, or sampling changes. |

MuseForge constructs the model style prompt as:

```text
English {genre} instrumental music, {mood} mood, {tempo} tempo,
featuring {instruments}. {brief}. A complete short song with a natural ending.
```

MuseForge fixes `cot="full"` for ordinary generation. Its explicit integration
smoke mode uses `cot="off"` and deterministic 32-token semantic sampling; that
mode produces a deliberately truncated diagnostic and must not be treated as a
completed song.

## Direct YuE2 request parameters

Calling `YuE2Pipeline` directly exposes controls that MuseForge does not expose
through its public API.

| Parameter | Accepted value and default | Effect | MuseForge behavior |
| --- | --- | --- | --- |
| `style` | String; required | Free-form description containing genre, instruments, vocal character, language, tempo, and other musical direction. | Constructed from the product controls and brief. |
| `tags` | String alias for `style` | Alternate name for `style`. Supplying both with different values is an error. | Not exposed. |
| `lyrics` | String; required | Words and section structure supplied to the model. | Exact user text is passed through. |
| `cot` | `full`, `melody`, or `off`; default `full` | `full` plans melody and chords; `melody` plans melody only; `off` skips symbolic planning. | Fixed to `full`, except explicit smoke tests. |
| `seed` | Integer in `[0, 2^63)`; default `831001` | Seeds model sampling. | Exposes the narrower unsigned 32-bit range. |
| `abc` | Non-empty ABC string or `None`; default `None` | Uses a supplied symbolic composition. Requires `cot=full` or `cot=melody`. | Not exposed. |
| `cfg_scale` | Finite float in `[0, 20]`, or `None` | Controls classifier-free text guidance. The effective default is 1.0 for `full`/`melody` and 1.01 for `off`. | Not exposed; native defaults apply. |
| `id` | Filename-safe identifier, 1–180 characters; default `song` | Labels the direct request and its saved metadata. | MuseForge uses its own job/version identities. |
| `abc_sampling` | `Sampling` object or partial dictionary | Overrides symbolic-plan sampling. | Not exposed; pinned defaults apply. |
| `semantic_sampling` | `Sampling` object or partial dictionary | Overrides semantic-audio-token sampling. | Not exposed; pinned defaults apply. |
| `cancelled` | Optional zero-argument callback | Returning true requests cooperative cancellation at supported checkpoints. | Connected to persisted job cancellation through the supervised child. |
| `on_token` | Optional callback | Receives generation progress from the token-producing stages. | MuseForge reports coarser stage progress instead. |

One call creates one candidate. Candidate ranking or selection is a separate
evaluation activity and is not performed automatically by the pipeline.

### Lyrics format and languages

Use section labels and separate sections clearly:

```text
[Verse]
First verse line
Second verse line

[Chorus]
First chorus line
Second chorus line
```

The YuE2-3B model card declares Chinese and English. The broader YuE project
documentation discusses multilingual lyrics, but it does not provide a Hindi
quality guarantee for this pinned YuE2 checkpoint. A local CUDA test passed
Devanagari text through the complete model and decoder: it produced 94.9 seconds
of valid, nontruncated 48 kHz stereo audio. That result establishes technical
compatibility only. Hindi pronunciation, intelligibility, and exact lyric
adherence have not been evaluated, so MuseForge continues to advertise English
only.

## Sampling and synthesis

Both `abc_sampling` and `semantic_sampling` accept a partial dictionary with the
following fields. Missing fields inherit the corresponding defaults.

| Field | Accepted range | ABC default | Semantic default | Meaning |
| --- | --- | --- | --- | --- |
| `temperature` | Finite float, 0–5 | 0.7 | 1.0 | Controls sampling randomness. Zero selects greedily. |
| `top_p` | Finite float, greater than 0 and at most 1 | 0.9 | 0.95 | Restricts sampling to a cumulative probability mass. |
| `top_k` | Integer, at least 1 | 30 | 100 | Restricts sampling to the highest-probability tokens. |
| `repetition_penalty` | Finite float, greater than 0 | 1.005 | 1.2 | Penalizes repeated tokens. |
| `penalty_window` | Integer, 1–100 | 100 | 50 | Number of recent tokens considered by the repetition penalty. |
| `min_tokens` | Integer, 0–`max_tokens` | 32 | 200 | Minimum tokens generated before normal termination. |
| `max_tokens` | Integer, at least 1 | 4096 | 9000 | Hard generation limit; reaching it can mark the result truncated. |

The pinned generation configuration uses a 24,576-token context and 32 midpoint
ODE synthesis steps. The runtime accepts a positive integer `ode_steps`, but
requires `ode_method="midpoint"` and `context=24576`. MuseForge does not expose
these controls.

Changing sampling, guidance, runtime versions, model revisions, decoders, or
devices can change a seeded result. The released defaults are the supported
starting point for normal generation.

## Loading and runtime parameters

`YuE2Pipeline.from_pretrained()` resolves model files and then constructs the
pipeline. These parameters affect loading and execution rather than musical
intent.

| Parameter | Accepted value and default | MuseForge behavior |
| --- | --- | --- |
| `model` | Hub ID or local directory; default `m-a-p/YuE2-3B` | Uses the pinned local model directory. |
| `vae` | Hub ID or local directory; default `m-a-p/YuE2-Vae` | Uses the pinned listening decoder. The legacy VAE is only for benchmark reproduction. |
| `revision`, `vae_revision` | Revision strings or `None` | Pinned immutable revisions are acquired and verified before startup. |
| `local_files_only` | Boolean; default false | Set true; workers run offline after acquisition. |
| `token` | Hub token or `None` | Used only during separate acquisition when required; never passed to the browser. |
| `cache_dir` | Path or `None` | Set to the configured weights cache. |
| `progress` | Boolean; default true | Child output is captured in bounded process logs. |
| `device` | `auto`, `cuda`, or `cpu`; default `auto` | MuseForge resolves saved `auto` to CUDA when usable, otherwise CPU. Explicit CUDA fails if unavailable. |
| `memory_budget_gib` | Integer GiB; runtime default 24 | Configured by `YUE2_MEMORY_BUDGET_GIB`; used for model loading/offload decisions. |
| `backend` | Runtime backend name; default `torch` | CUDA uses `torch`; CPU uses `torch-eager`. |
| `quantization` | Runtime mode; default `none` | Fixed to `none`. |
| `offload_ar` | Boolean; default false | Controlled by `YUE2_OFFLOAD_AR`; may lower GPU pressure by offloading the autoregressive model. |
| `verify_hashes` | Boolean; default true | Retained. MuseForge also verifies the external weights against its manifest. |
| `vae_core_frames` | Positive runtime-specific frame count or `None` | Not exposed; native decoder chunking applies. |
| `generation_config` | `GenerationConfig` or `None` | Uses the model's pinned configuration. |

Only the startup device probe may choose CPU as an automatic fallback. A failed
job never switches devices or substitutes mock output.

## Direct usage examples

These examples target the installed 0.1.6 Python interface. Pin revisions and
use local files for a reproducible deployment.

### Normal generation

```python
from yue2 import YuE2Pipeline

with YuE2Pipeline.from_pretrained(
    "/weights/model",
    vae="/weights/vae",
    device="cuda",
    local_files_only=True,
) as pipe:
    song = pipe(
        style="English acoustic folk, warm lead vocal, guitar and tabla, calm medium tempo",
        lyrics="[Verse]\nMorning opens by the river\n\n[Chorus]\nCarry the song home",
        cot="full",
        seed=42,
    )
    song.save_artifacts("outputs/english-folk")
    print(song.truncated)
```

### Hindi technical probe

```python
song = pipe(
    style="Hindi acoustic folk, warm vocal, tabla and guitar, calm medium tempo",
    lyrics=(
        "[Verse]\nसुबह की धूप नदी पर आई\nमन में नई उमंग जगाई\n\n"
        "[Chorus]\nचलो मिलकर गीत सुनाएँ\nसपनों की दुनिया सजाएँ"
    ),
    cot="off",
    seed=42,
)
song.save_artifacts("outputs/hindi-probe")
```

This direct example bypasses MuseForge's English-only capability check. Treat
the result as experimental until a listening evaluation verifies the language.

### Sampling overrides

```python
song = pipe(
    style=style,
    lyrics=lyrics,
    cot="full",
    seed=42,
    abc_sampling={"temperature": 0.6, "top_k": 24},
    semantic_sampling={"temperature": 0.9, "top_p": 0.92},
)
```

### Save and resume a symbolic plan

```python
from yue2 import SymbolicPlan

plan = pipe.plan(style=style, lyrics=lyrics, cot="full", seed=42)
plan.save("outputs/plan")

restored = SymbolicPlan.load("outputs/plan")
semantic = pipe.generate_semantic(restored)
latents = pipe.synthesize(semantic)
audio = pipe.decode(latents)
```

`SymbolicPlan.load()` restores an unchanged saved plan and validates its files.
To edit a composition, copy the exported `score.abc` and submit the edited ABC
as a new request with `cot="full"` or `cot="melody"`.

## Outputs, truncation, and limitations

`song.save_artifacts()` retains audio, the ABC score when applicable, plan
metadata, semantic tokens, acoustic latents, effective configuration, timings,
model identities, and integrity records. Inspect `result.json` and both the ABC
and semantic truncation flags. A playable file can still be incomplete when a
token limit was reached.

The current evidence does not establish:

- exact singing of supplied lyrics or reliable pronunciation in any language;
- Hindi language fidelity, despite successful technical generation;
- guaranteed instrumental-only or vocal output;
- exact adherence to instruments, mood, genre, or tempo;
- a requested output duration;
- deterministic output across environments;
- reference-audio conditioning, continuation, or audio editing through the
  current MuseForge provider route.

MuseForge validates the media container, sample rate, channel count, finite
samples, silence and clipping thresholds before publication. Those checks prove
technical audio validity, not musical or linguistic quality.

## Sources

- [Official YuE2 generation guide](https://github.com/multimodal-art-projection/YuE/blob/main/docs/generation.md)
- [Official YuE2-3B model card and Python examples](https://huggingface.co/m-a-p/YuE2-3B)
- [Official YuE2 example request](https://huggingface.co/m-a-p/YuE2-3B/blob/main/examples/tonight-awake.json)
- [Official YuE2 generation defaults](https://huggingface.co/m-a-p/YuE2-3B/blob/main/yue2_generation_config.json)
- [Official YuE project prompt guidance](https://github.com/multimodal-art-projection/YuE/blob/main/README.md#prompt-engineering-guide)

Some upstream model-card snippets still show older inference-wheel versions.
For MuseForge, the installed 0.1.6 signatures and the repository lock take
precedence when they differ from those examples.
