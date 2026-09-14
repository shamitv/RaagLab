# Phase 2 API

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

Project editing, user retry, iterations, archive/duplicate, settings, and library operations are reserved for later phases.

## Phase 03 workspace endpoints

`PATCH /api/v1/projects/{id}` accepts any nonempty subset of `title`, `draft` (the validated Generation contract), and `active_version_id` (a version in the same project, or null). Supply `If-Match: "<revision>"`. Each successful patch returns the next revision and ETag; manual selection also increments the selection epoch, including reselecting the same version. Omitted revision headers return 428 and stale revisions return 412. Generated content is never rewritten by these patches.

`PATCH /api/v1/versions/{id}` accepts `label` and/or boolean `favorite`, with the same revision-header requirements. Favorites live in the workspace/version relation. Both version detail and version listing expose the favorite state. Version detail includes its ETag.

`POST /api/v1/versions/{id}/iterations` accepts `{ "operation": "refine|variation|regenerate|lyrics_edit", "inputs": <Generation> }` and requires `Idempotency-Key`. It returns the ordinary 202 Accepted job identity and Location. The source determines project and parentage. Refine requires a nonblank `inputs.iteration_instruction`; lyrics_edit requires user lyrics. Reusing an operation/source/key with changed intent returns 409. Each operation uses the transactional outbox, separate worker, leases, cancellation and terminal commit pipeline.

For lyrics_edit, musical inputs are preserved from the immutable source; only submitted user lyrics and the instruction change. The worker links the original audio artifact and emits `audio_recomposed: false`. Other operations publish new audio artifacts. Variation from the UI requests a new seed; regeneration retains the source seed. The mock provider records musical intent without promising semantic audio edits or sung lyrics. Structure remains null because this provider supplies no timed sections.

Migration `0002_version_favorites` adds the favorite relation without modifying the frozen foundation migration. Existing projects and version content remain intact.
