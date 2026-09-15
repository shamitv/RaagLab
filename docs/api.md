# API

The API container serves the browser and `/api/v1` on the same origin. `/docs` and `/openapi.json` describe request and response types; regenerate the checked-in TypeScript definitions with `npm run types:api` after exporting OpenAPI as described in development.md.

`POST /generations` requires `Idempotency-Key` (16–128 characters). Submit a brief, one or more instruments, and a mood. Language defaults to English, genre to Indie Pop, tempo to Medium, vocals to Instrumental, lyrics mode to mock, and duration to 8 seconds. Seed is an optional unsigned 32-bit integer. Include `project_id` to append to a project; otherwise acceptance creates one. The 202 response includes job/project IDs, a status URL, and a browser project URL. Its Location header is the status URL. Acceptance commits without contacting RabbitMQ.

Identical key and validated intent returns the same job even after completion; a different intent returns 409. Keep the original key when retrying an uncertain HTTP submission. A generated seed is persisted once and cannot change on replay. Invalid/unsupported controls return 422; payloads over 128 KiB return 413. User lyrics retain exact Unicode, line breaks, spaces, and stanza labels.

- `POST /projects`: create an empty project, optionally with a validated draft; 201 with Location and ETag.
- `GET /projects` and `GET /projects/{id}`: list/detail; detail includes jobs and active version. Lists accept `limit` (1–100, default 20) and opaque `cursor`, and return `items`/`next_cursor`.
- `GET /jobs/{id}`: authoritative state, stage, dispatch state, attempts, provider readiness, and result/error links.
- `POST /jobs/{id}/cancel`: cancel queued work immediately (200); running work returns 202 while cancellation is pending. Terminal outcomes are unchanged.
- `GET /projects/{id}/versions` and `GET /versions/{id}`: immutable result snapshots, exact lyrics, provenance, and audio metadata/URL.
- `GET /capabilities`: supported product vocabulary, instrumental demo limitations, independent lyrics modes, and observed worker readiness.
- `GET`/`HEAD /artifacts/{id}`: WAV with Content-Length, ETag, Accept-Ranges, safe filename and byte-range support. Unsatisfiable ranges return 416; missing/unsafe stored objects return 410 while version details remain inspectable.

Errors contain a safe code/message, retryability, correlation ID, and optional validation field locations. Database failures return 503. An offline worker does not prevent acceptance into a configured queue. No storage key, secret, database URL, or broker address is returned.

Project, job, version, library, workspace preference and template routes live under `/api/v1`. Project and version identifiers are UUIDs scoped to the configured workspace.

## Phase 03 workspace endpoints

`PATCH /api/v1/projects/{id}` accepts any nonempty subset of `title`, `draft` (the validated Generation contract), and `active_version_id` (a version in the same project, or null). Supply `If-Match: "<revision>"`. Each successful patch returns the next revision and ETag; manual selection also increments the selection epoch, including reselecting the same version. Omitted revision headers return 428 and stale revisions return 412. Generated content is never rewritten by these patches.

`PATCH /api/v1/versions/{id}` accepts `label` and/or boolean `favorite`, with the same revision-header requirements. Favorites live in the workspace/version relation. Both version detail and version listing expose the favorite state. Version detail includes its ETag.

`POST /api/v1/versions/{id}/iterations` accepts `{ "operation": "refine|variation|regenerate|lyrics_edit", "inputs": <Generation> }` and requires `Idempotency-Key`. It returns the ordinary 202 Accepted job identity and Location. The source determines project and parentage. Refine requires a nonblank `inputs.iteration_instruction`; lyrics_edit requires user lyrics. Reusing an operation/source/key with changed intent returns 409. Each operation uses the transactional outbox, separate worker, leases, cancellation and terminal commit pipeline.

For lyrics_edit, musical inputs are preserved from the immutable source; only submitted user lyrics and the instruction change. The worker links the original audio artifact and emits `audio_recomposed: false`. Other operations publish new audio artifacts. Variation from the UI requests a new seed; regeneration retains the source seed. The mock provider records musical intent without promising semantic audio edits or sung lyrics. Structure remains null because this provider supplies no timed sections.

Migration `0002_version_favorites` adds the favorite relation without modifying the frozen foundation migration. Existing projects and version content remain intact.

## Phase 04 project, library, and workspace routes

`GET /api/v1/projects` accepts `q`, `archived=active|archived|all`, `limit` (1–100, default 20), and an opaque `cursor`. Search matches project titles. Pages use stable `(created_at, id)` ordering; cursors are bound to the search/archive filters and reject reuse with different filters. The default `active` view omits archived projects. `GET /api/v1/projects/{id}` reopens the project draft, active version, and recent job history.

`PATCH /api/v1/projects/{id}` adds `archived` to the existing conditional title/draft/selection patch. Send the project ETag as `If-Match`; a missing header returns 428 and a stale revision returns 412. Archiving a project with queued or running work returns 409. Archive retains all history and artifact references. `POST /api/v1/projects/{id}/duplicate` creates `Copy of <title>` with new project and version IDs, a remapped completed-version parent graph, the same selected version, and `origin_version_id` links. Pending jobs and idempotency/attempt records are not copied. Audio artifacts are shared by reference and remain protected from collection.

`GET /api/v1/library` returns completed versions from active projects, newest first by default. It accepts `q` (project title or version label), `favorite_only`, `genre`, `language`, `sort=recent|oldest`, `limit`, and `cursor`. The cursor is stable and bound to the full filter/sort selection. Items report favorite and audio availability. Version labels and favorites are changed with the conditional `PATCH /api/v1/versions/{id}` described above.

`GET /api/v1/settings` returns an ETag/revision. `PATCH /api/v1/settings` requires `If-Match` and accepts a nonempty subset of `generation_defaults`, `volume` (0–1), `repeat_mode` (`off|one|all`), and `export_format` (`wav`). Missing and stale revisions return 428 and 412 respectively. Initial defaults are Piano, Calm, English, Indie Pop, Medium tempo, Instrumental, 8 seconds, mock lyrics, volume 0.8, repeat off, and WAV export.

`GET /api/v1/templates` and `/api/v1/templates/{id}` expose five original revision-1 starter templates. Template application is a browser draft action; it does not create a job or start generation. Generation remains an explicit user action.

`POST /api/v1/jobs/{id}/retry` requires `Idempotency-Key` and is allowed for failed or timed-out jobs. It creates a new job linked through `retry_of_job_id`; replaying the same key returns that job. The new job keeps the source execution snapshot, provider route and lyrics checkpoint. The original operation remains in the snapshot, so retrying a lyrics-only edit still reuses its source audio. Retry jobs cannot themselves be retried, preventing chains. The original failed/timed-out record is unchanged.

If an artifact is missing or unsafe, artifact playback returns 410 and version/library metadata remains inspectable with `available: false`. A successful later read can restore the availability flag after the object returns. Missing media is never replaced with generated content implicitly.

Migration `0003_workspace_settings` adds revisioned settings and the verified project/library and recovery indexes. It follows `0002_version_favorites`; existing applied migrations are not rewritten. See [development](development.md) for safe artifact inspection/collection and full Phase 04 verification commands.

The current release schema head is `0004_worker_runtime`; apply it with the
guarded `bash scripts/migrate.sh` command before starting an upgraded stack.
The mock release and persistence evidence is recorded in the [Phase 06 release
report](implementation/evidence/06/20260915-090415-d55061e8/README.md). The
normal-mode CPU YuE2 release gate is separately tracked and requires a host
with at least 32 GiB available memory and the verified weights volume.
