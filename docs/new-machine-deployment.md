# Deploy MuseForge on a new machine

This guide prepares MuseForge for either the YuE2 song provider or the mock provider. YuE2 requires separately licensed weights and suitable CPU or NVIDIA GPU resources. The mock provider is an explicit evaluation option that needs no GPU, weights, host Python, or host Node.js.

## 1. Prepare the host

Use a Linux host, or Ubuntu under WSL 2 with Docker Desktop integration enabled. Install:

- Git
- Docker Engine or Docker Desktop using Linux containers
- Docker Compose v2.24.4 or newer

Confirm the engine before cloning:

```bash
docker info --format '{{.OSType}}'
docker compose version
git --version
```

The first command must print `linux`.

## 2. Clone and configure

```bash
git clone <repository-url> musicgen
cd musicgen
bash scripts/setup.sh
```

`setup.sh` creates a private `.env` from `.env.example` only when one does not already exist. Review these common settings:

```dotenv
APP_PORT=8000
CONTAINER_RESTART_POLICY=unless-stopped
# SONG_LINK_BASE_URL=https://music.example.test
```

- Change `APP_PORT` if the port is occupied.
- Set `CONTAINER_RESTART_POLICY=no` when containers should remain stopped after Docker or WSL restarts.
- Set `SONG_LINK_BASE_URL` only to an HTTP(S) origin that already routes back to this application and is reachable by the device scanning the QR code. Do not include credentials, query parameters, or a fragment. MuseForge does not configure DNS, TLS, a reverse proxy, firewall access, or authentication.

The default application binding is `127.0.0.1`, so it is accessible only from the host. Keep that default unless a separate, trusted proxy provides access.

## 3. Set up with the mock provider

To evaluate the application with generated demo audio instead of YuE2, explicitly select the mock provider:

```bash
bash scripts/start.sh mock
```

Open the URL printed by the command, normally `http://127.0.0.1:8000`. The startup builds images, starts PostgreSQL and RabbitMQ, applies migrations, starts the API, dispatcher and mock worker, and waits for health checks. Mock audio is intended for product setup and workflow testing; it does not represent model-generated songs.

To build and create stopped containers for a later maintenance window:

```bash
bash scripts/start.sh mock --create-only
docker compose --env-file .env --profile mock start
```

After a manual `docker compose start`, confirm readiness before using the product:

```bash
curl --fail http://127.0.0.1:8000/health/ready
```

## 4. Verify and operate

```bash
bash scripts/smoke.sh mock
bash scripts/logs.sh
docker compose --env-file .env --profile mock ps
```

Generate a song in the browser, open **My Songs**, and confirm playback and download. If `SONG_LINK_BASE_URL` is configured, scan the downloaded QR code from another device and confirm that the song page opens.

Stop the deployment without deleting songs or database data:

```bash
bash scripts/stop.sh
```

The `database`, `broker`, and `artifacts` named volumes survive normal `down` and subsequent startup. Do not use `docker compose down --volumes` unless permanent data deletion is intended and backed up.

## 5. Managed Ubuntu/WSL deployment

The managed scripts create a private environment under `$HOME/.local/share/museforge-ubuntu1`, generate database and broker passwords, and use the Compose project name `museforge-ubuntu1`. This example explicitly starts the mock provider:

```bash
bash scripts/deploy/setup.sh
bash scripts/deploy/start.sh mock
```

Use a different location or project name when running multiple deployments:

```bash
MUSEFORGE_DEPLOY_ROOT="$HOME/.local/share/museforge-secondary" \
MUSEFORGE_PROJECT_NAME=museforge-secondary \
APP_PORT=8001 \
bash scripts/deploy/setup.sh
```

Pass the same two `MUSEFORGE_...` variables to later deployment commands. Create-only is also supported:

```bash
bash scripts/deploy/start.sh mock --create-only
```

See the [operations runbook](deployment/machines/ubuntu1/runbook.md) for backup, restore, update, rollback, drain, and recovery procedures.

## 6. YuE2 song-provider deployment

YuE2 requires the exact external `musicgen-yue2-test_weights` Docker volume described by the [deployment manifest](deployment/machines/ubuntu1/deployment-manifest.md). The weights are not stored in Git or application images, and their license and hashes must be reviewed before provisioning them on a new host.

After the volume and NVIDIA Container Toolkit are available, select the device and start real mode:

```bash
YUE2_DEVICE=auto bash scripts/deploy/start.sh real
```

Use `YUE2_DEVICE=cuda` for strict GPU startup or `YUE2_DEVICE=cpu` for explicit CPU inference. Missing weights or strict CUDA support causes startup to fail; MuseForge does not substitute mock audio. Real generation has substantial memory and warmup requirements. Follow the [model integration boundary](model-integration.md) and [deployment handoff](deployment-handoff.md) before enabling it.

## Troubleshooting

- **Port already allocated:** inspect the owner with `docker ps`, stop the intended deployment, or choose another `APP_PORT`.
- **UI opens but generation is unavailable:** check `bash scripts/logs.sh` and `/health/ready`; verify that the selected worker is healthy.
- **Containers return after a Docker restart:** set `CONTAINER_RESTART_POLICY=no`, recreate the containers, and stop them explicitly.
- **WSL shell restart changes nothing:** Docker Desktop may restore containers with `restart: unless-stopped`; use the restart policy above.
- **QR opens nowhere:** the encoded `SONG_LINK_BASE_URL` must be reachable from the scanning device and route to the same persistent deployment.
