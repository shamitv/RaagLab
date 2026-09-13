# Part 1: Initialize and implement the portable MuseForge AI application

You are the coding agent responsible for initializing this repository and implementing MuseForge AI, a web application that turns a song brief into lyrics and playable music, then supports non-destructive iteration and version history.

Start by producing a detailed phase-by-phase implementation plan and writing the planning files described below. Then implement the phases in dependency order, keeping those files current. If the user explicitly requests a planning-only run, produce the plan and do not implement application code during that run. Otherwise, proceed after documenting the plan; routine implementation choices do not require a separate approval step.

This prompt covers the portable application, its containers, and a working mock deployment for development and validation. The companion prompt, `docs/prompts/02-machine-deployment.md`, covers deployment to a particular WSL or native Linux machine and activation of a real model. Do not make WSL a dependency of the application.

## 1. Read the project context before designing the implementation

Inspect the repository, its applicable instructions, and any existing code before making changes. Preserve existing work and adapt your plan to what is actually present.

Use these files as the product and visual references:

- `design.md`: MuseForge AI product behavior, responsive layouts, visual tokens, components, and acceptance criteria.
- `docs/ui mockups/mockup_desktop.png`: desktop visual reference.
- `docs/ui mockups/mockup_mobile.png`: mobile visual reference.

Read the design document and inspect both images. If a reference is unavailable, record that fact and continue from the available specification. Keep the existing design and images intact.

The core experience is:

1. Enter a song brief and choose instruments, mood, language, genre, tempo, and vocal type.
2. Supply lyrics, use a static example, or request mock-generated lyrics.
3. Submit a music-generation job.
4. See the job move through queued and processing states.
5. Read the lyrics and play the resulting audio.
6. Apply a refinement or create a variation as a new version.
7. Switch between versions without losing previous inputs, lyrics, audio, or lineage.
8. Save and reopen projects through persistent backend storage.

Do not infer that a particular model has already been selected from the repository directory name `musicgen`. In particular, do not silently select a model just because it shares that name.

## 2. Architectural requirements

Implement the following architecture:

```text
Browser
  |
  | One origin: built UI, JSON API, job status, audio downloads
  v
API service ---------------------------------------------------+
  | Serves the compiled static UI                              |
  | Validates requests and exposes application endpoints       |
  | Persists jobs, projects, versions, and metadata             |
  |                                                           |
  +----> PostgreSQL <----------------------- Model worker       |
  |        |                                  ^               |
  |        | Durable dispatch/outbox records   |               |
  |        v                                  |               |
  |     Dispatcher ----> Durable message queue-+               |
  |                                           |               |
  |                         Model worker container             |
  |                         - mock provider initially          |
  |                         - real model provider later        |
  |                         - writes status and results        |
  |                                           |               |
  +----> Artifact storage <-------------------+               |
         API reads audio; worker writes audio                 |
                                                              |
Browser gets progress and playable artifacts from the API <---+
```

The dispatcher is a lightweight process using the application codebase. It publishes persisted work; it does not perform inference. A small transactional outbox is the preferred dispatch mechanism. An equivalent recovery mechanism is acceptable if you explain how it closes the database-commit/message-publication failure window and prove that behavior with a test.

Mandatory boundaries:

- The API must not load model weights or execute model inference inside request handlers or API background tasks.
- Generation commands must travel through a real broker to a separate worker container. An in-memory queue or eager task execution is insufficient for the end-to-end milestone.
- The model worker container is the service that will eventually host the actual model. Its initial implementation uses a mock provider behind the same interface.
- PostgreSQL is the authoritative application store, including durable job status. Do not substitute SQLite for integration acceptance tests.
- Store audio and other binary artifacts in artifact storage, with references and metadata in PostgreSQL. Do not pass audio bytes, base64 audio, or weights through the queue.
- For the initial single-host deployment, a shared persistent volume is sufficient. Keep the storage interface independent of a particular host path. A future worker on another host will need shared or object storage; a Docker volume alone does not provide that.
- The browser communicates only with the API. It must not connect to the broker, database, or worker container directly.
- Build the frontend into static assets and serve those assets from the API service in the normal packaged deployment. A separate frontend runtime server is not required.
- A frontend development server is allowed for hot reload, with an API proxy, but the acceptance tests must also run against the UI served by the API container.
- Use the same application source and service contracts on WSL and native Linux. Platform differences belong in deployment configuration and scripts.

Default to a small monorepo and the following stack unless existing code gives a good reason to choose otherwise:

| Concern | Default |
| --- | --- |
| API | Python, FastAPI, Pydantic |
| Persistence | PostgreSQL, SQLAlchemy, Alembic migrations |
| Queue and task execution | RabbitMQ and Celery |
| UI | React, TypeScript, Vite |
| Packaging | Separate API and worker images, Docker Compose |
| Initial artifacts | Filesystem storage adapter backed by a named volume |
| Backend verification | pytest and integration tests against actual services |
| Browser verification | Playwright or an equivalent browser automation tool |

Choose mutually compatible supported versions during planning and pin them in manifests, lockfiles, and image configuration. Record meaningful departures from these defaults in a short architecture decision record. Keep the API and mock-worker dependency sets free of heavyweight inference dependencies. Do not add a second broker, an independent task-result database, Kubernetes, or additional services without a concrete need.

With Celery, persist product-facing results and status in the application database; Celery's transient task state must not become the product's source of truth.

## 3. Plan and track every phase in Markdown

Before application implementation, create:

```text
docs/implementation/
  master-plan.md
  status.md
  decisions/
    0001-application-architecture.md
  phases/
    00-discovery-and-contracts/
      plan.md
      status.md
      todo.md
    01-foundation/
      plan.md
      status.md
      todo.md
    02-mock-end-to-end/
      plan.md
      status.md
      todo.md
    ...one directory per planned phase...
```

After a phase has been implemented and its exit criteria verified, create its `implementation-status.md`. Do not create reports claiming that future phases have been implemented. If a phase cannot finish, record its partial work and blockers in `status.md` and leave its completion report absent.

`master-plan.md` must describe the architecture, scope, assumptions, phase dependencies, deliverables, acceptance criteria, major risks, test strategy, and the boundary between Part 1 and machine deployment in Part 2. Include a phase summary table and map the important requirements in this prompt and `design.md` to phases.

Use the following minimum contents for each phase's files. Fill them with concrete information; do not leave the actual plan as a collection of empty templates.

### `plan.md`

```markdown
# Phase NN: <name>

## Objective
<User-visible outcome and why this phase is needed.>

## Dependencies and entry criteria
<Required earlier phases, decisions, services, or inputs.>

## Scope
<Features and behavior included in this phase.>

## Work breakdown
<Ordered tasks, affected modules, and planned deliverables.>

## Contracts and data changes
<API, queue, provider, schema, migration, and configuration changes.>

## Acceptance criteria
<Observable conditions that must hold before completion.>

## Verification
<Commands and automated/manual checks to prove those conditions.>

## Risks, assumptions, and deferred work
<Specific uncertainties and destination phases for deferred scope.>
```

### `status.md`

```markdown
# Phase NN status

- State: not_started | in_progress | blocked | completed
- Started: <timestamp or not started>
- Last updated: <timestamp>
- Completed: <timestamp or not completed>
- Current focus: <task or milestone>

## Completed work
<Actual work with file or evidence references.>

## Remaining work
<Unfinished requirements and acceptance checks.>

## Blockers and decisions needed
<Concrete blocker, impact, and next action; or none.>

## Latest verification
<What ran, result, and evidence location.>

## Next action
<The next actionable step.>
```

### `todo.md`

```markdown
# Phase NN to-do

- [ ] NN-01 <specific implementation task>
- [ ] NN-02 <specific integration task>
- [ ] NN-03 <acceptance verification task>
- [ ] NN-04 Update documentation and create implementation-status.md
```

Use stable task identifiers. Add enough detail to make each item actionable. Check items only after performing them. Explain any removed or moved task and link its destination.

### `implementation-status.md`, created when the phase closes

```markdown
# Phase NN implementation status

- Outcome: completed
- Completed at: <timestamp>
- Implemented scope: <brief description>

## Changes delivered
<Features, affected files, migrations, configuration, and contracts.>

## Acceptance results
| Criterion | Result | Evidence |
| --- | --- | --- |
| <criterion> | passed | <command result, test, screenshot, or artifact> |

## Verification performed
<Exact commands or procedures, outcomes, and environment.>

## Deviations from the plan
<What changed, why, and implications.>

## Remaining limitations and follow-ups
<Non-blocking limitations with linked future tasks; or none.>

## Handoff
<How to run this result and what the next phase can rely on.>
```

Keep `docs/implementation/status.md` synchronized as the overall summary. Update phase status at meaningful milestones and before ending a work session. A phase is complete only when its required acceptance criteria pass; tests that were not run must be identified as not run. If code is finished but an environment-dependent check is blocked, report that distinction instead of claiming verification.

When resuming work, read these files and continue from the actual state. Do not reinitialize completed phases. If implementation changes after a phase closes, append a dated correction or reopen that phase so its report remains accurate.

## 4. Suggested repository organization

Adapt naming to the chosen tools, but keep these responsibilities separate:

```text
apps/
  api/                         # HTTP routes, composition, static UI serving
  web/                         # React application and frontend tests
services/
  worker/                      # Queue consumers and model lifecycle
  dispatcher/                  # Outbox publication and recovery process
packages/
  domain/                      # Shared domain rules and database access
  contracts/                   # Typed API, job, and provider schemas
  providers/                   # Lyrics and music provider interfaces/adapters
  storage/                     # Artifact storage interfaces/adapters
migrations/                    # Alembic migrations
tests/
  integration/
  e2e/
fixtures/                      # Small, deterministic, redistributable demo assets
deploy/
  docker/                      # API and worker Dockerfiles
  compose/                     # Portable development/production overrides
scripts/                       # Setup, test, smoke, and operational entry points
docs/
  implementation/
  architecture.md
  development.md
  api.md
  model-integration.md
  deployment-handoff.md
compose.yaml
.env.example
README.md
```

Avoid creating empty packages just to match this tree. A simpler layout is acceptable if API, inference, contracts, storage, and UI boundaries remain clear. Keep model weights, generated audio, local secrets, caches, and database data out of source control.

## 5. Deliver a working mock system early

The first usable milestone must exercise this entire path:

```text
UI -> API -> PostgreSQL job/outbox -> broker -> worker container
   -> mock provider -> audio artifact + persisted result
   -> API job polling -> UI playback
```

Only the expensive generation behavior should be mocked in this milestone. The browser calls real endpoints; the API uses real PostgreSQL; the task crosses a real queue; the worker runs as a separate container; the audio is a real decodable file.

Implement independently selectable providers:

- `LyricsProvider`: initially supports user-provided lyrics, static fixtures, and deterministic mock generation.
- `MusicProvider`: initially a deterministic mock that returns an audible sample or creates a short valid WAV file without weights, credentials, GPU access, or paid services.

The mock provider must:

- Accept the same normalized request and emit the same result schema as a real provider.
- Run inside the worker, not inside browser code.
- Produce playable audio with accurate duration, content type, sample rate, and channel metadata.
- Use original, generated, or clearly redistributable fixtures with provenance recorded.
- Support configurable stage delays and controlled success, failure, timeout, and cancellation scenarios for tests.
- Return deterministic metadata and fixture selection for a given request or seed where practical.
- Identify its output as demo/mock audio in the product. Do not imply that the fixture sings the user's supplied lyrics.
- Support several queued requests without leaking one project's result into another.

Provide a usable lyrics input mode selector. Preserve user-provided lyrics exactly unless the user explicitly edits or requests changes. Mock/static lyrics must be labelled appropriately. A paid lyrics service or a local lyrics LLM is not required for Part 1 or for the first real-music deployment.

Do not make frontend-only mock handlers the default deployed workflow. They may be used for isolated component tests, but they are not evidence that the application is integrated.

## 6. API, static hosting, and job contracts

Use a versioned API namespace, such as `/api/v1`, with typed request and response models and generated OpenAPI documentation. Validate the brief limit, musical selections, lyrics size, and provider-supported duration/options on the server as well as in the UI.

Plan and implement endpoints covering at least:

| Capability | Suggested route |
| --- | --- |
| Create/list projects | `POST /api/v1/projects`, `GET /api/v1/projects` |
| Read/update a project | `GET /api/v1/projects/{id}`, `PATCH /api/v1/projects/{id}` |
| Submit a generation | `POST /api/v1/generations` |
| Read authoritative job state | `GET /api/v1/jobs/{id}` |
| Request cancellation | `POST /api/v1/jobs/{id}/cancel` |
| Explicitly retry a failed job | `POST /api/v1/jobs/{id}/retry` |
| List/read versions | `GET /api/v1/projects/{id}/versions`, `GET /api/v1/versions/{id}` |
| Iterate or branch a version | `POST /api/v1/versions/{id}/iterations` |
| Select an active version | `PATCH /api/v1/projects/{id}` with `active_version_id` |
| Stream/download artifacts | `GET /api/v1/artifacts/{id}` |
| Read provider options/readiness | `GET /api/v1/capabilities` |
| Read/save preferences and list templates | Appropriate `/api/v1/settings` and `/api/v1/templates` routes |
| Process liveness/dependency readiness | `/health/live`, `/health/ready` |

Route names may differ if the same behavior is clearly documented. Add routes needed by implemented library actions, such as rename, favorite, duplicate, and archive/delete, with explicit semantics.

Generation submission must return promptly with HTTP `202 Accepted`, a stable job ID, project ID, initial state, and a status URL. Do not hold a browser HTTP request open for the duration of inference.

Use an idempotency key for generation submissions. Repeating the same key and payload must return the same logical job; reusing the key for a conflicting payload must return a clear conflict. Scope keys and persist them in the database. Define automatic retry as another attempt of the same job, and an explicit user retry as a new linked job using the preserved request snapshot.

Persist a complete normalized request snapshot, including operation, source version, lyrics source/content, musical parameters, provider/model revision where known, and seed. Worker execution must not depend on mutable browser state or a project's later edits.

Provide a versioned JSON queue envelope containing at least a message ID, schema version, job ID, correlation ID, dispatch timestamp, and intended provider/capability route. The worker can fetch the immutable request from PostgreSQL by job ID. Validate queue messages and reject unsupported schema versions clearly. Use JSON-safe serialization rather than executable serialization formats.

Static hosting must satisfy all of the following:

- Build frontend assets during the API image build, preferably in a separate build stage, and copy only the build output into the API runtime image.
- Serve the SPA entry page and versioned assets from the API's origin.
- Use relative API and artifact URLs; do not hard-code machine names or `localhost` in frontend source.
- Support direct navigation and refresh on valid client-side routes, such as `/projects/<id>`.
- Keep API, health, artifact, and documentation routes outside the SPA fallback. Missing API endpoints and missing asset files must return the correct errors, not `index.html` with status 200.
- Give hashed assets appropriate long-lived caching and make the entry document revalidate so upgrades load the correct bundle.
- Stream audio with correct media headers and byte-range behavior for browser seeking. Validate artifact identifiers and prevent traversal outside the artifact store.
- Use same-origin requests in packaged deployment; limit any development CORS configuration to the configured development origin.

Consult the selected framework version's [FastAPI static-file documentation](https://fastapi.tiangolo.com/tutorial/static-files/) when implementing asset hosting. Explicitly verify SPA routing behavior; mounting a directory is not proof that application routes refresh correctly.

Start with job polling with a bounded interval and backoff, pausing or reducing work when appropriate. Polling is sufficient. If you add server-sent events, retain the job-status endpoint as the recovery mechanism, define reconnect behavior, and do not rely on process memory for durable status.

## 7. Persistence, versions, and artifacts

Design migrations for at least these logical entities:

- Projects: identity, title, editable input draft, save state/version token as appropriate, active version, timestamps.
- Song versions: project, parent version, version number, label, immutable generation inputs, lyrics, artifact references, actual duration, structure, operation/iteration request, provider provenance, creation time.
- Generation jobs: request snapshot, state, stage, nullable progress, attempt count, error information, cancellation request, scheduling/claim/heartbeat timestamps, result version, retry relationship, and idempotency information.
- Artifacts: storage key, media type, byte size, checksum where practical, duration/sample rate/channels for audio, and lifecycle metadata.
- Outbox/dispatch records: the durable publication state needed to recover interrupted submissions.
- Settings/preferences and favorites as needed for the implemented product flow.

Use UUIDs or similarly robust identifiers, timezone-aware timestamps, foreign keys, useful indexes, and explicit migration files. Use relational columns for identity, relationships, and operational queries; JSONB is appropriate for flexible generation settings and metadata. Apply migrations through a controlled migration command/service rather than racing multiple API processes at startup.

Define these consistency rules:

- Every successful generation or applied refinement creates a new version. Existing generated content remains immutable.
- Create Variation records the selected source version as the parent; Regenerate preserves the submitted inputs unless changed by the user.
- Changing the active version changes only selection. It does not delete or regenerate history.
- Allocate version numbers safely under concurrent completion. Do not rely on an unprotected `MAX(number) + 1` calculation.
- A late completion must not unexpectedly replace a newer version the user has selected. Define and test the rule for automatic activation versus manual selection.
- A job cannot create multiple final versions merely because its task message is delivered more than once.
- Switching versions updates audio, lyrics, structure, and iteration context together.
- Failed and cancelled jobs remain inspectable without creating misleading completed versions.
- Reference artwork, duration, and song structures in the design are examples. Derive runtime metadata from the actual output. Mark estimated structure as estimated; never fabricate alignment or section timestamps beyond the audio duration.

Persist the essential generation record immediately so closing the browser does not lose a job. Define Save Project as saving the current project title/draft/selection and relevant organization metadata. Local autosave preserves unsent edits; it is not the only copy of completed server-generated results. Define how local drafts reconcile with saved server revisions and avoid silently overwriting newer data.

Write artifacts to temporary locations, validate them, and publish them atomically before marking a job successful. Plan recovery/cleanup for orphaned files and missing artifacts. Retention must respect artifacts referenced by other versions; a lyrics-only version may reuse an existing audio artifact with an explicit indication that the audio has not been recomposed.

## 8. Queue reliability and worker lifecycle

Treat delivery as at least once and design for duplicate execution attempts. A database write followed by an untracked queue publish is not a complete reliable submission implementation.

Implement and document:

- Durable queues/messages, reliable publication, persisted dispatch retries, and reconciliation of jobs that were committed but not published.
- Transactional job claiming or an equivalent ownership mechanism, bounded leases/heartbeats, and fencing so an expired or superseded attempt cannot overwrite a later outcome.
- Acknowledgment only in accordance with the selected task framework's actual failure semantics.
- Bounded retry with backoff for transient errors; validation errors and repeated out-of-memory failures must not enter an endless retry loop.
- Queue routing that prevents mock workers from consuming real-model jobs or incompatible workers from consuming requests they cannot satisfy.
- A documented lifecycle covering queued, running, retrying, cancellation requested, cancelled, succeeded, failed, and timed-out outcomes. Distinguish dispatch state and current generation stage where useful.
- Persistent cancellation. A queued job must not start after cancellation. A running provider should stop cooperatively if supported; otherwise explain the delay and prevent a late result from being published as success after cancellation wins.
- Clear timeout, worker restart, broker restart, and orphaned-job recovery behavior.
- Safe handling of the race between cancellation and successful completion; terminal state must not oscillate.
- Structured logs correlated by job ID and attempt ID, with no secrets or full lyrics/prompts logged by default.
- Worker readiness/capability registration or equivalent observable status, separate from API process health.

Check [Celery's task and acknowledgment documentation](https://docs.celeryq.dev/en/stable/userguide/tasks.html) for the selected version. Late acknowledgment alone does not cover every worker-loss case; make the recovery strategy explicit and test it.

For future GPU workers, begin with one active inference job per worker/GPU and conservative prefetch. Choose a process model compatible with the selected ML runtime, and load the model inside the process that performs inference. Do not initialize a GPU model in a parent process and then assume arbitrary forking is safe. Verify that cancellation checks and heartbeats still function while inference is busy.

Keep the model loaded between jobs when supported. Model initialization, warm-up, and readiness must be separate from ordinary API startup. An unavailable worker should produce a clear availability/status indication rather than blocking the application from serving the user's existing projects.

## 9. Implement the specified UI as a functioning product

Follow `design.md` and the supplied mockups for layout, typography, blue-forward tokens, component hierarchy, desktop navigation, mobile bottom navigation, and accessibility.

Build the composer, musical controls, lyrics input/result, music preview, iteration surface, song structure, and version history. Implement the core Create, Library, Projects, and Settings flows. Templates can start as a small static collection. Collaboration, billing/upgrade, notifications, and multi-user permissions can be explicit later scope; any corresponding reference UI must be omitted or clearly presented as unavailable rather than pretending it works.

Required behavior includes:

- Brief validation and a live character count, wrapping instrument chips, single-select mood/language, and the specified musical attribute controls.
- Lyrics source selection with an accessible editor for user-supplied text and correct preservation of non-Latin scripts and stanza labels.
- Input preservation while jobs queue, run, fail, or reconnect.
- Stage text and cancellation where meaningful. Display determinate progress only if the provider supplies meaningful progress; otherwise use an indeterminate state.
- Real playback, pause, seeking, elapsed/total time, and download of the returned artifact.
- An accessible waveform or seek control based on the audio. A simplified initial rendering is acceptable; a decorative waveform must not claim to be measured audio data.
- Functional favorite, rename, duplicate, version navigation, and repeat controls where exposed. Define the playback collection used by previous/next/shuffle, or disable controls that have no valid action.
- Copy/edit lyrics, regenerate, change mood/instruments, apply a refinement, create a variation, and switch versions.
- A conservative interpretation of free-text iteration in mock mode, with clear demo behavior. When real semantic editing is unsupported, preserve the instruction and explain the supported action rather than claiming a precise audio edit occurred.
- Empty, queued, running, partial-result where supported, completed, failed, cancelled, and offline/reconnecting states.
- Keyboard navigation, named icon buttons, appropriate chip semantics, visible focus, screen-reader progress announcements, touch targets, reduced-motion handling, and accessible player controls.
- Local draft recovery, server-backed project reopening, and a lightweight save confirmation/error state.

Check the specified desktop and mobile widths, including 1440 px desktop, 390 px mobile, and narrower widths around 320–360 px. The design's fixed rail and column minimums can exceed a 1440 px viewport when combined; resolve that with responsive grid adjustments while preserving the visual hierarchy and the no-horizontal-page-scroll requirement. Record any material design tradeoff.

Do not copy the mockups' example track length or version count into live results. Do not autoplay audio unexpectedly. Do not display a button as functional when its action is only a placeholder.

## 10. Real-model integration boundary

Define typed provider interfaces with operations equivalent to:

- `capabilities()` and readiness/health information.
- Request normalization and validation.
- `generate(request, progress_callback, cancellation_token)`.
- Result validation and artifact metadata.
- Explicit errors for invalid requests, unsupported capabilities, transient failures, initialization failures, and resource exhaustion.

Design capabilities to represent model identity/revision, supported languages, instrumental generation, vocal generation, conditioning on exact supplied lyrics, duration limits, sample rates, seed behavior, progress reporting, and supported refinement/continuation operations.

Keep these product capabilities distinct:

1. Generating or displaying text lyrics.
2. Generating instrumental music from a text description.
3. Generating vocals.
4. Generating vocals that sing the exact user-provided lyrics.
5. Editing, extending, or conditioning on previously generated audio.

Support for one must not be reported as support for the others. A lyrics panel beside an instrumental output is a valid early milestone, but it is not proof of lyric-conditioned singing. Disable or explain unsupported model controls and record the mismatch with the full product target.

Configuration should independently select lyrics and music providers, for example `LYRICS_PROVIDER=user|static|mock` and `MUSIC_PROVIDER=mock|<adapter-name>`. Also support configurable model ID/revision, weights/cache directories, device, precision, duration/resource limits, timeouts, and concurrency without editing application source.

If a model has already been explicitly selected, implement its adapter against verified documentation and isolate its dependencies in the real-worker image. If no model is selected, complete the interface, mock implementation, capability handling, packaging boundary, and documented adapter contract in Part 1. Assign selection and the concrete adapter to Part 2's real-model phase; do not create a fake real provider or claim real inference is complete.

The real worker must fail clearly if its required weights or device are unavailable. Do not silently fall back to mock audio during a real-model deployment.

## 11. Packaging and configuration

Provide a reproducible Compose-based startup path with API, PostgreSQL, broker, dispatcher, and a mock worker. Provide a clean way to select a real worker later without accidentally running competing mock and real consumers for the same jobs. Use profiles or override files deliberately and document the resolved services. [Docker Compose profiles](https://docs.docker.com/compose/how-tos/profiles/) can select optional services; verify profile dependencies instead of assuming they start automatically.

Include:

- An API image that builds and serves the UI and contains no weights or GPU runtime.
- A lightweight CPU-only mock-worker image or build target.
- A separate real-worker build path with model-specific dependencies when selected.
- Persistent volumes for PostgreSQL, broker durability, generated artifacts, and model cache as appropriate.
- Health checks, startup dependency handling, migration commands, restart behavior, and clean shutdown.
- Configuration for database/broker URLs, storage paths, provider choices, queue names, limits, host port, public origin if needed, and log levels.
- `.env.example` containing documented placeholders and safe development defaults, with actual secret files ignored by version control.
- A default host port published on loopback for single-user local use. The API must still bind to an appropriate container interface so the published port works.
- Database and broker reachable on the internal container network, with administrative host ports disabled unless explicitly enabled for development.
- Distinct host and container paths and no hard-coded Windows drive letters, `/mnt/c` paths, or personal home directories in application code.
- Scripts for setup, start/stop, migration, demo seeding, logs, smoke tests, and tests. Stopping the app must preserve data; data-reset commands must be separate and explicit.

Use a clearly stated local single-user security boundary for the initial release. Multi-user authentication and internet exposure are separate scope unless requested. Leave room for ownership and access checks; do not present an unauthenticated local deployment as a public multi-user service.

## 12. Proposed phase sequence

Use this sequence as the baseline. You may split or adjust phases if dependencies remain clear, the early integrated mock milestone remains early, and all required scope is assigned.

| Phase | Deliverable | Exit criteria |
| --- | --- | --- |
| 00: Discovery and contracts | Repository audit, architecture, schema/API/provider decisions, complete phase documentation | The plan is actionable, assumptions and deferred model choices are explicit, and every planned phase has plan/status/to-do files |
| 01: Foundation | Repository structure, locked dependencies, migrations, core configuration, API static UI shell, broker/DB/worker containers | The documented mock stack starts; API serves the built shell; required services and migration path work |
| 02: Mock end-to-end | A simple but usable composer, real job submission/queue/worker path, lyrics modes, playable mock result, basic persistence | A browser submits a job through real services, plays actual audio, and retrieves the job/result after refresh without weights or credentials |
| 03: Complete responsive workspace | Visual implementation of the core design, full player, lyrics editor, meaningful states and accessibility | Desktop/mobile browser checks pass against the API-served UI; displayed controls perform their stated actions |
| 04: Projects, versions, and recovery | Save/reopen/library flows, immutable versions and branches, idempotency, cancellation, retry, crash/dispatch recovery | Earlier versions survive iteration; duplicates and restarts preserve consistent results; failure cases have verified recovery behavior |
| 05: Provider readiness | Capability-driven UI/API, real-provider integration contract, isolated image/configuration path, adapter if already selected | Mock remains fully functional; unsupported capabilities are explicit; Part 2 can integrate the selected real provider without redesigning UI/API/queue contracts |
| 06: Release verification and handoff | Relevant automated checks, packaged smoke test, operational/development docs, machine-deployment handoff | A clean environment can run the integrated mock app using documented steps; completed phases have evidence-based implementation reports |

Provide a demonstrable checkpoint after Phase 02. Do not defer the first browser-to-worker integration until the UI is polished or a real model is available.

## 13. Verification and acceptance

Use focused tests for domain rules and meaningful integration/browser tests for system behavior. Do not spend effort on tests that merely restate trivial styling or implementation details.

At minimum, verify:

1. A clean configured checkout builds and starts the mock stack using documented commands.
2. The API container serves the actual UI, including refresh of a nested client route; nonexistent API and asset routes are not swallowed by the SPA fallback.
3. A browser-created generation crosses the real broker, runs in the worker container, persists a job/version in PostgreSQL, and returns decodable audible media.
4. User lyrics survive submission and retrieval exactly; static and mock modes are distinguishable.
5. Browser refresh and API restart do not lose jobs, project selection, or completed versions.
6. Iteration creates a new version with a correct parent, and selecting an old version does not destroy newer results.
7. Duplicate submissions, duplicate queue delivery, and simultaneous job completion do not create duplicate final versions or conflicting version numbers.
8. A committed-but-unpublished job is recovered after dispatch interruption; a lost worker has a bounded, visible recovery outcome.
9. Failure, retry, cancellation before start, cancellation during generation, and cancellation/completion races preserve coherent state and prior results.
10. Playback seeking works through the API artifact route; artifact traversal and invalid identifiers are rejected.
11. The desktop/mobile core flow works with the specified responsive layouts and keyboard navigation, without horizontal page scrolling.
12. The UI displays actual metadata and honest provider capabilities; real-provider failures cannot masquerade as successful mock inference.

Keep GPU-dependent checks separate and opt-in. CI and the normal Part 1 test suite must not download model weights or require a GPU, paid endpoint, or private token.

If the current environment cannot run containers or a browser, complete the independently verifiable work and report the exact remaining acceptance checks. Do not label the entire integrated application verified based only on unit tests.

## 14. Final deliverables and first response

Deliver the source code, migrations, container configuration, configuration examples, small demo fixtures, relevant tests, current phase records, and documentation for architecture, development, API/contracts, model integration, and deployment handoff.

The deployment handoff must specify the working mock command, required service connections, storage expectations, migration process, image/provider selection, model capabilities still needed, and any real-model work explicitly deferred to Part 2. Include a clear status split between implemented, tested, mocked, and pending.

Your first response must contain a concise repository assessment, proposed architecture/stack, assumptions, and phase plan. Write the detailed plan into the required Markdown files before implementing application code. Continue through the authorized phases and keep the records synchronized.

Your final implementation response must state what works, how to start the API-served application, what verification actually ran, where the phase reports are, and any remaining limitations. Do not claim machine deployment or real-model inference until those have actually been performed.
