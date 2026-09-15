# MuseForge AI

Turn a musical idea into a playable song. Describe the sound, choose instruments, mood, language, genre and lyrics, then let MuseForge generate and save the result. **My Songs** keeps every completed version ready to play, download, favorite, or revisit from a QR code.

![MuseForge My Songs screen](docs/implementation/evidence/07/20260915-song-first/my-songs-desktop.png)

## Create, listen, and return

1. Open **Create**, describe the song, and choose its musical controls.
2. Generate it. Progress, cancellation, retry, and draft recovery remain available while MuseForge works.
3. Open the result from **My Songs** to play it, read its lyrics, download the audio, or create another version.
4. Configure `SONG_LINK_BASE_URL` with an address reachable by your phone to copy or download a permanent song QR code.

![MuseForge mobile song screen](docs/implementation/evidence/07/20260915-song-first/song-mobile.png)

## Model used

MuseForge uses the open-source [`m-a-p/YuE2-3B`](https://huggingface.co/m-a-p/YuE2-3B) model with the [`m-a-p/YuE2-Vae`](https://huggingface.co/m-a-p/YuE2-Vae) listening decoder. The deployment pins the model, decoder, and `yue2-infer==0.1.6` runtime to verified revisions instead of downloading a changing latest release at startup. The model weights are licensed under CC BY-NC 4.0.

The app turns the selected genre, instruments, mood, tempo, language, and music brief into YuE2's style prompt and supplies the user's structured lyrics separately. Ordinary generation uses full symbolic planning and produces validated 48 kHz stereo audio. MuseForge currently exposes the verified English route; a Hindi CUDA probe completed technically, but Hindi pronunciation and lyric adherence have not been evaluated. YuE2 also does not guarantee exact lyrics, instrumental-only output, prompt fidelity, or requested duration.

See the [YuE2 parameter reference](docs/yue2-parameters.md) for every supported model input, sampling default, runtime option, example, and MuseForge mapping. The [model integration boundary](docs/model-integration.md) records the evidence behind the capabilities shown in the product.

## Set up MuseForge

The standard setup creates a real YuE2 environment and the standard start command selects the real provider:

```bash
bash scripts/setup.sh
bash scripts/start.sh
```

This requires the verified weights volume and suitable CPU or NVIDIA GPU resources. `DEVICE=auto` uses CUDA when the Docker engine exposes the NVIDIA runtime.

### Mock provider

Use the mock provider when you want to evaluate the product without installing YuE2 weights or configuring a GPU:

```bash
bash scripts/setup.sh mock
bash scripts/start.sh mock
```

Open the printed address, normally `http://127.0.0.1:8000`. Set `APP_PORT` in `.env` when that port is occupied. This command explicitly selects the mock provider, which creates clearly labelled demo audio. For generated songs, follow the real YuE2 deployment section in the [new-machine deployment guide](docs/new-machine-deployment.md). YuE2 has narrower documented capabilities; generated audio may not follow requested lyrics, vocals, musical controls, or exact duration.

```bash
bash scripts/start.sh mock --create-only
```

Set `CONTAINER_RESTART_POLICY=no` in `.env` to prevent containers from returning after Docker restarts. The default is `unless-stopped`.

```bash
bash scripts/logs.sh
bash scripts/migrate.sh
bash scripts/stop.sh
bash scripts/test.sh unit
```

Data volumes survive normal stop/start. Start with the [new-machine deployment guide](docs/new-machine-deployment.md). See the [development guide](docs/development.md), [deployment handoff](docs/deployment-handoff.md), [model boundary](docs/model-integration.md), [YuE2 parameter reference](docs/yue2-parameters.md), and [Phase 07 plan](docs/implementation/phases/07-song-first-experience/plan.md) for deeper reference.

QR links remain useful while their configured base address, this server, and the saved song are available. Network exposure, authentication, and public hosting are operator responsibilities.
