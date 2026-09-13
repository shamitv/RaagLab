# Application contracts and data decisions

- Contract baseline: 1
- Decision date: 2026-09-13
- State: Phase 01 foundations and Phase 02 generation/provider/artifact interfaces are implemented; later-phase endpoints remain planned. See [Phase 02 report](phases/02-mock-end-to-end/implementation-status.md).
- Related: [ADR 0001](decisions/0001-application-architecture.md), [job reliability](job-reliability.md), [UI behavior](ui-behavior.md)

## Common conventions and validation

All public application routes use `/api/v1`; health and OpenAPI routes are separate. IDs are UUIDs; timestamps are timezone-aware UTC ISO 8601. Lists use opaque keyset cursors, stable `(created_at, id)` ordering and a bounded page size (default 20, maximum 100). Never expose a storage key, database URL, broker address, or secret to the browser.

Pydantic request/response models produce OpenAPI and generated TypeScript types. Reject unknown request fields instead of silently dropping unsupported options. Error responses have `code`, safe `message`, optional field errors, `retryable`, and `correlation_id`. Use 422 for validation/unsupported options, 404 for absent objects, 409 for conflicting idempotency/invalid state, 412 for stale `If-Match`, 428 for required revision headers omitted, and 503 for a missing configured provider route or unavailable required API storage dependency.

| Field | Planned server and UI rule |
| --- | --- |
| `brief` | Non-whitespace content; at most 500 Unicode code points; preserve original line breaks/content; count with equivalent code-point logic in JS and Python |
| `instruments` | One or more unique values: Guitar, Piano, Tabla, Drums, Bass, Strings, Synth |
| `mood` | Exactly one: Happy, Melancholic, Romantic, Energetic, Calm, Epic |
| `language` | Exactly one: Hindi, English, Hinglish, Punjabi, Tamil; this describes lyrics/intent and is not proof of sung-language support |
| `genre` | Indie Pop default; Pop, Folk, Ambient, Rock, Electronic as initial catalogue; provider capability restrictions apply |
| `tempo` | Slow 60–90, Medium 100–120 default, or Fast 130–160 BPM; store label and bounds; unsupported exact BPM control is not exposed |
| `vocal_type` | Instrumental, Male Vocals, Female Vocals, Mixed Vocals as product vocabulary; unsupported vocals are disabled and explained |
| `lyrics` | `mode=user|static|mock`; user text required in user mode; maximum 20,000 code points / 80,000 UTF-8 bytes; reject invalid Unicode; preserve supplied text exactly |
| `duration_seconds` | Integer; mock range 5–30, default 8; use capability bounds for any real provider; never silently shorten |
| `seed` | Optional unsigned 32-bit integer; when omitted choose once at job acceptance and persist the effective value |
| `iteration_instruction` | Optional exact text up to 2,000 code points; required for free-text refinement; retain even if semantic editing is unsupported |
| Titles/labels | Nonblank, maximum 120 code points; organization metadata is editable without altering generated content |

The demo selects Instrumental by default and explains that the reference Male Vocals option requires a capable real provider. Musical selectors in mock mode express saved intent; the UI states that demo audio does not faithfully implement genre, mood, instruments, or lyrics. Preserve all written reference choices across widths. Request bodies are capped at 128 KiB; lyrics are plain text rendered without HTML interpretation. Whitespace validation does not trim or Unicode-normalize user lyrics. Preserve stanza labels and native scripts on every retrieval/retry/version operation.

## HTTP surface and ownership phases

| Route | Semantics and responses | First phase |
| --- | --- | --- |
| `POST /projects` | 201; create an empty project with draft, revision and no active version | 02 |
| `GET /projects`, `GET /projects/{id}` | Saved project summary/detail; include active version and inspectable job links; list filters/query/archive support added in 04 | 02, 04 |
| `PATCH /projects/{id}` | Conditional title/draft/active-version/archive update; return new ETag/revision; reject a version from another project | 03–04 |
| `POST /generations` | 202; accept a job for an existing project or atomically create a project when `project_id` is absent | 02 |
| `GET /jobs/{id}` | Authoritative state/stage/progress, attempts, cancellation state, result/version links, safe error and readiness context | 02 |
| `POST /jobs/{id}/cancel` | Persist cancellation; 200 if already terminal, 202 if running cancellation remains pending; return authoritative state | 02, hardened 04 |
| `POST /jobs/{id}/retry` | 202; only failed/timed-out jobs; new job linked by `retry_of_job_id`, using original preserved execution inputs | 04 |
| `GET /projects/{id}/versions`, `GET /versions/{id}` | Stable complete result snapshots; never substitute the currently active version for a requested ID | 02 |
| `POST /versions/{id}/iterations` | 202; a new job for `refine`, `variation`, `regenerate`, or `lyrics_edit`; selected source version becomes parent | 03 |
| `PATCH /versions/{id}` | Update label/favorite organization metadata only; revision/ETag required; generated fields forbidden | 03 |
| `POST /projects/{id}/duplicate` | 201; duplicate draft and all completed version history; fresh IDs and remapped parents; artifacts shared by reference | 04 |
| `GET /library` | Completed versions across non-archived projects; query, favorites, genre/language filters and documented sort | 04 |
| `GET /artifacts/{id}` | Stream actual media; support GET/HEAD, single byte range, download filename; no arbitrary path parameter | 02 |
| `GET /capabilities` | Product vocabulary, independently configured providers, effective supported options, limits, demo flag and readiness age | 02, audited 05 |
| `GET /settings`, `PATCH /settings` | Versioned workspace preferences: generation defaults, playback volume/repeat, available export format; conditional save | 04 |
| `GET /templates`, `GET /templates/{id}` | Small versioned original static catalogue; applying one changes draft only | 04 |
| `/health/live`, `/health/ready` | Process liveness; DB/migration/artifact-read readiness; report dispatcher/broker/worker degradation separately | 01, extended 02 |
| `/openapi.json`, `/docs`, `/redoc` | Generated API documentation, protected from SPA fallback | 01 |

Route paths in this table are relative to `/api/v1` except the final two rows. A project archive uses `PATCH {archived: true}` with undo; permanent deletion is not exposed in Part 1. An archive cannot complete while nonterminal jobs exist: return `active_jobs_conflict`, with a UI path to cancel/wait and then archive. Existing archived projects can be explicitly opened/unarchived; generation requires unarchiving. Label the player action Archive project, not Delete track.

Duplication copies completed versions with `origin_version_id`; `generation_job_id` is null on copied rows so the original job-to-result uniqueness is preserved. It copies no pending jobs, idempotency records or attempts. Remap active selection and parents within the duplicated graph. Favorite is version-level local organization metadata; the library and player share that record.

## Generation and idempotency

All job-creating endpoints require `Idempotency-Key` (opaque 16–128 characters). Scope uniqueness to `(workspace_id, operation_namespace, key)`. Store it with a hash of canonical client intent before executing the command. Canonicalization sorts object keys and normalizes declared defaults only where stable; it preserves lyric text and array meaning. Keep this intent hash separate from the fully normalized execution snapshot so a later provider/default change does not change the meaning of an already accepted replay.

Same key plus same client payload returns the existing logical job and its current state, even after completion. Same key plus different payload returns 409. Concurrent requests resolve against the unique database constraint; only the winner creates the project/job/outbox record. Keys stay as long as the generation record. No in-memory cache is the sole idempotency implementation. Apply the same policy to explicit retry and iteration endpoints.

Generation returns promptly (local acceptance target: under 1 second in the mock acceptance environment, excluding cold startup) without waiting for the broker or provider. A 202 body contains `job_id`, `project_id`, `state`, `status_url`, and relative project URL; set `Location` to the status URL. `GET /jobs/{id}` returns a stable resource for reconnection and retry inspection.

Persist a versioned execution snapshot with operation, workspace/project/source-version IDs, brief, all musical controls, lyrics source and exact supplied content, static fixture ID/revision where applicable, provider IDs/revisions/capability snapshot, model ID/revision when known, seed, requested/effective duration, instruction, and relevant resource/time limits. Store produced lyrics once as a durable job checkpoint before music. Automatic attempts reuse that checkpoint; explicit retry copies it when available. Never read mutable browser/project drafts during execution.

Distinguish automatic attempts on one logical job from explicit retries that create another linked job. A retry preserves the original provider/model selection; if it is no longer available, report that fact rather than silently selecting another provider. A fresh regeneration command may use visibly edited inputs; source ID remains its parent. Default regenerate copies source inputs into the editing surface; require an explicit edit before changing them.

## Database entities and constraints

Use a single local workspace row, UUID keys, UTC timestamps, explicit foreign keys and migrations. Shared tables carry `workspace_id`; repository access is scoped to it. This is a future ownership boundary, not authentication.

| Table | Key content and constraints |
| --- | --- |
| `workspaces` | Local singleton identity and schema-independent settings scope |
| `projects` | Title, JSONB editable draft, `revision`, `active_version_id`, `selection_epoch`, `latest_submission_seq`, `next_version_number`, archive timestamps |
| `song_versions` | Project/parent/origin IDs, number, editable label/revision, immutable inputs/lyrics/structure/provenance, `generation_job_id`, audio-recomposed flag, timestamps |
| `generation_jobs` | Immutable request/intent hash, operation/source, state/stage/progress, attempts/deadlines, cancellation, result version, retry link, captured selection epoch/submission sequence |
| `job_attempts` | `(job_id, attempt_number)` unique; worker, fence token, lease, heartbeat/start/end, typed outcome/error; no raw prompt/lyrics logs |
| `idempotency_records` | Unique scope/key, canonical intent hash, linked job and resource response identity |
| `outbox_messages` | Message/schema/job/correlation IDs, route, dispatch sequence, state, claim token/expiry, publication count, next publication time, confirmation/error timestamps |
| `artifacts` | Unique opaque storage key, SHA-256, bytes/media type, measured sample rate/channels/duration, published/available/retired lifecycle timestamps |
| `version_artifacts` | Version/artifact role links; several versions may reference the same audio; FK prevents deleting referenced rows |
| `worker_registrations` | Worker/provider/model identity, capability revision, readiness, last heartbeat and expiry |
| `workspace_settings`, `version_favorites` | Conditional preference revision and unique workspace/version favorite relation |

Enforce unique `(project_id, number)` and unique non-null `song_versions.generation_job_id`. Add same-project parent/active-version constraints using composite keys where possible and transactional checks where cyclic references require staged insertion. Initial project active version is null. Index jobs by state/next action/deadline, outbox by state/next publication, attempts by lease expiry, versions by project/order, and project/library organization queries. Flexible metadata uses JSONB with schema versions; query-critical state stays relational.

Migration increments: 01 creates workspace/project/job/outbox/attempt/artifact/version/registration foundations; 03 adds organization metadata only if absent; 04 adds settings/favorites indexes and any recovery refinements. Do not rewrite an applied migration. `migrate` is a one-shot command using a PostgreSQL advisory lock and Alembic upgrade to the chosen head, never an API startup race.

## Version and selection transactions

The worker locks the project row, verifies the current job claim, allocates `next_version_number`, inserts one complete version plus artifact links, and marks the job successful in one database transaction. Allocation is an increment under lock, not an unprotected maximum query. No version is inserted for failed/cancelled/timed-out work. Parentage is taken from the immutable snapshot. Generated content cannot be patched in place.

On submission, increment the project's `latest_submission_seq` and capture it and `selection_epoch` on the job. Manually selecting a version increments `selection_epoch`, even when reselecting the same version. Auto-activate a completed version only if both the captured epoch is unchanged and the job is still the latest submission. Otherwise add the version to history and announce its availability without moving selection. Automatic retries keep the same sequence; a user retry is a new submission. Both auto-activation and manual selection increment project revision so stale saves fail safely.

UI version selection loads a single version detail and swaps audio, lyrics, structure, and iteration context together; stop old playback and reset position without autoplay. Never update the lyrics panel and audio source from different asynchronous selections. Editable unsent composer changes remain a separate draft with explicit source context.

## Draft and Save Project semantics

Jobs/results persist immediately, independently of Save. Save Project conditionally saves title, current editable draft, active selection, and organization metadata using ETag/`If-Match`. A saved response returns the new revision. The generation snapshot records exactly what was submitted even when the saved draft later changes.

Use IndexedDB for local draft text/selections, base server revision and last edit timestamp; debounce writes within 250 ms and flush at meaningful transitions. Do not store completed audio as the authoritative result. On reopen, compare revisions: restore a dirty local draft only when its base matches; otherwise show server and local choices and let the user keep local edits, use server, or save a copy. A 412 never silently overwrites either draft. On reconnect, fetch status/versions before enabling dependent actions. Warn on leaving when remote save failed and unsynced edits remain; successful local draft storage alone must not be mistaken for a server save.

## Provider interfaces and capability schema

Define typed `LyricsProvider` and `MusicProvider` interfaces with `capabilities`, `readiness`, `normalize/validate`, and `generate(request, progress_callback, cancellation_token)`. Initialize inside the executing worker process, independently of API startup. The cancellation token checks persisted cancellation and lease ownership. Results are validated at the provider boundary and again before publication.

| Capability/result field | Meaning |
| --- | --- |
| `provider_id`, `provider_revision`, `model_id`, `model_revision`, `is_demo` | Exact provenance; null model fields for mock, never a fabricated real identity |
| `lyrics_text`, `text_to_instrumental`, `vocals`, `exact_lyrics_vocals` | Separate booleans; mock lyrics supports text, demo music does not claim semantic text-to-music/vocals |
| `languages` | Distinguish lyrics text acceptance from verified audio/vocal language conditioning |
| `operations` | Separate full generation, lyrics edit, variation/regeneration, audio edit, continuation and audio conditioning |
| `duration`, `sample_rates`, `channels`, `seed_behavior` | Supported bounds/formats and reproducibility qualifications |
| `progress_mode`, `cooperative_cancel`, `readiness` | Meaningful determinate progress versus none; busy/offline/initializing/ready and last observed time |
| `lyrics_source`, `audio_recomposed`, `warnings` | Source labels, unchanged-audio disclosure, capability limitations |
| Result artifact and structure | Storage reference, byte size/checksum, measured duration/rate/channels; optional sections explicitly estimated or measured |

Typed errors: invalid request, unsupported capability, transient infrastructure/provider failure, initialization failure, resource exhaustion, deadline exceeded, and cancellation. Mock/static lyrics and original fixture provenance are distinct from user lyrics. Free-text mock refinement retains the instruction and generates another labelled demo; it does not claim precise semantic editing. Lyrics-only refinement creates a new version while reusing the source audio with `audio_recomposed=false`.

Configuration independently chooses `LYRICS_PROVIDER=user|static|mock` as the default and allows the configured supported lyrics modes in the editor; `MUSIC_PROVIDER=mock|<selected-adapter>`. Unsupported explicit choices fail validation. Model ID/revision, weights/cache directories, device/precision, duration/resource limits, timeout, concurrency, and queues are configuration. There is no real adapter until Part 2 selects one. Real mode with missing adapter/weights/device must fail clearly and may never fall back to mock.

## Static hosting and artifact protocol

API image stages install frozen frontend dependencies, build `apps/web/dist`, and copy only those assets into the Python runtime. Serve hashed `/assets/*` with immutable long-lived caching and revalidate the entry document. Use a client-route allowlist for HTML fallback (`/`, `/create`, `/projects`, `/projects/{uuid}`, `/library`, `/settings`, `/templates`); exclude `/api`, `/health`, `/assets`, and documentation. Unknown API routes, missing assets, and unsupported paths return actual 404 errors. A UUID client route can load the SPA and then display a project-not-found API result.

Artifact lookup validates UUID and workspace, resolves only a stored generated key, verifies containment under the configured root, and rejects symlinks/path escapes. Serve correct `Content-Type`, `Content-Length`, safe `Content-Disposition`, ETag and `Accept-Ranges`. Support valid single ranges with 206, unsatisfiable ranges with 416 and total size, and HEAD without a body. No open redirect, untrusted filename, or file path is accepted. Missing referenced audio yields a clear unavailable/410 result and inspectable version; no substitute demo audio is served.

Write and validate temporary audio within the artifact filesystem, then atomically rename to an attempt-specific final key before database success. Never overwrite another attempt's object. Record accurate duration/sample rate/channels and SHA-256; use original 16-bit PCM WAV mock output with deterministic seed selection, default 8 seconds, 44.1 kHz stereo. Derive metadata from the actual file. Initial structure may be absent or estimated and must stay within measured duration. Orphan cleanup and retention rules are defined in [job reliability](job-reliability.md).
