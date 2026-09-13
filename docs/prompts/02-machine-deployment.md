# Part 2: Deploy MuseForge AI and its real model on a specific machine

You are the coding and deployment agent responsible for deploying the MuseForge AI application and activating its real music-generation model on the target machine.

Start with a phase-by-phase deployment plan and create the phase tracking files specified below. Then execute the deployment in dependency order. If the user explicitly requests a planning-only run, deliver the plan without deploying during that run. Otherwise, continue through the authorized deployment work after recording your plan.

Read `docs/prompts/01-portable-application.md`, the existing implementation records, and the actual repository. Reuse the portable application, API-served static UI, PostgreSQL, queue, dispatcher, storage, and model-worker boundaries. Do not reinitialize or replace the application merely to deploy it.

The intended first target is a Linux environment inside WSL on a Windows machine. WSL is optional: another deployment may run entirely on native Linux. Support both deployment paths through the same application source and Linux container images, with separate host instructions and configuration where necessary.

The authoring workspace was `C:\work\musicgen`; treat this as a starting clue, not a required deployment path. Discover the actual repository location, target host, WSL distribution if applicable, container engine, and hardware. Do not assume a particular GPU, amount of VRAM, Linux distribution, model, or installed driver.

## 1. Define the deployment outcome

The required deployed path is:

```text
Browser on the user's machine
  -> API endpoint serving the compiled UI and application API
  -> PostgreSQL-backed job submission
  -> durable queue
  -> model worker container with the selected real model loaded
  -> persisted audio artifact and job/version result
  -> API playback/download endpoint
  -> browser playback, iteration, and project reopening
```

First prove this path on the target machine with the mock provider. Then replace the music provider with a compatible real model while retaining the same browser/API/job contracts. Lyrics may remain user-provided, static, or mocked; a real lyrics LLM is not a prerequisite.

The deployment must provide:

- A working API-served UI reachable through a documented local URL.
- Persistent PostgreSQL data, generation artifacts, and model cache across ordinary restarts.
- A real worker that receives generation jobs through the queue and produces actual model output.
- Verified capability handling: instrumental output, vocals, and exact supplied-lyric conditioning are distinct features.
- Reproducible start, stop, update, recovery, and backup/restore procedures.
- Host-specific settings kept out of portable application logic.
- Accurate phase reports distinguishing completed work, observed behavior, and unverified portability claims.

Do not create external cloud infrastructure or substitute a hosted inference API for the requested local model deployment unless the user changes the scope.

## 2. Audit the application and inspect the host before changing it

Read the applicable repository instructions, `README.md`, `design.md`, implementation master plan/status, architecture decisions, Compose files, Dockerfiles, environment examples, model integration notes, and deployment handoff.

Check whether the portable mock milestone was actually verified. Identify missing release prerequisites such as unfinished migrations, artifact range requests, queue routing, or incomplete model-provider contracts. Fix deployment-critical gaps in the existing code and update their implementation records; do not silently hide them in machine setup scripts.

Collect a focused, non-secret machine inventory:

| Area | Information to determine |
| --- | --- |
| Host | Windows with WSL or native Linux, OS/version, CPU architecture |
| WSL, when used | Distribution name, WSL version, kernel, default user, service/startup behavior, existing integration |
| Compute | CPU count, available RAM, swap, resource limits |
| Storage | Available space, filesystem/mount type, chosen source/data/cache locations |
| GPU | Vendor, model, available VRAM, driver, visibility at each applicable layer |
| Container runtime | Engine location, active Docker context, version, Compose availability, permissions, GPU integration |
| Network | Available application port, browser-to-service path, proxy/offline constraints if present |
| Existing state | Existing MuseForge services, volumes, database contents, model files, and processes using the selected ports |
| Model | Any explicitly selected model, weights/revision already present, access requirements, known capabilities |

Use appropriate read-only commands for the actual platform. Examples include `wsl --status` and `wsl --list --verbose` on Windows; `uname`, `/etc/os-release`, `nproc`, `free`, and `df` in Linux; and `docker version`, `docker info`, `docker context show`, `docker compose version`, and vendor GPU tools where installed. Do not assume every example command is available or meaningful on every host.

If more than one plausible target distribution or host exists, identify the ambiguity early and request the missing target choice while continuing repository review and planning. If the target is clear, proceed without a routine confirmation question.

Record observed facts separately from assumptions. Do not copy credentials, tokens, full environment dumps, or unrelated personal information into inventory documents or logs.

## 3. Plan and track the deployment in Markdown

Use a separate deployment record so machine work does not overwrite portable implementation history:

```text
docs/deployment/
  master-plan.md
  status.md
  portability-matrix.md
  machines/
    <machine-alias>/
      inventory.md
      deployment-manifest.md
      runbook.md
      verification.md
      phases/
        D00-inventory-and-plan/
          plan.md
          status.md
          todo.md
        D01-host-preparation/
          plan.md
          status.md
          todo.md
        D02-mock-deployment/
          plan.md
          status.md
          todo.md
        D03-real-model/
          plan.md
          status.md
          todo.md
        D04-system-validation/
          plan.md
          status.md
          todo.md
        D05-operations-and-handoff/
          plan.md
          status.md
          todo.md
```

Create `implementation-status.md` inside each phase directory only when that phase is implemented and its exit criteria pass. It is the completion report for the deployment work in that phase. An incomplete or blocked phase must instead have an accurate `status.md` and open to-do items.

For each phase:

- `plan.md`: objective, dependencies, actual target, scope, ordered tasks, files/configuration to change, validation steps, exit criteria, assumptions, and recovery/rollback implications.
- `status.md`: state (`not_started`, `in_progress`, `blocked`, or `completed`), start/update/completion timestamps, completed work, remaining work, blockers, latest verification, and next action.
- `todo.md`: concrete checkboxes with stable identifiers; mark them only after performing the work and move deferred tasks explicitly.
- `implementation-status.md`: actual changes, acceptance results with evidence, commands run and their outcomes, deviations, limitations, and handoff to the next phase.

Keep the overall deployment status synchronized. If operating on a later machine, create a new machine directory and preserve earlier deployment results. Use a neutral machine alias, not secrets or personal account identifiers.

The master plan must assign every required deployment outcome to a phase, specify which steps differ between WSL and native Linux, and distinguish application defects from host/environment blockers.

## 4. Choose the appropriate host topology

### WSL target

Use WSL 2 for the containerized GPU path when supported by the actual machine. Determine which container-engine topology is already in use:

1. Docker Desktop on Windows with integration into the selected WSL distribution; or
2. A Docker Engine running directly inside the WSL distribution.

Choose one topology for this deployment and document it. Reuse a working engine and context when possible. Do not accidentally install a second competing engine or switch an existing context without understanding the effect on its containers and volumes. Docker Desktop is not an application requirement.

Use Linux filesystem locations for the deployed source, model cache, and data where practical, rather than putting heavy container/model I/O under a Windows-mounted project directory. If the repository is currently under a Windows drive, create or synchronize an appropriate Linux working copy while preserving the source of truth and relevant uncommitted changes. Record the relationship between the authoring and deployment directories. Do not delete or move the original workspace as an incidental deployment step. See [Docker's WSL backend guidance](https://docs.docker.com/desktop/features/wsl/) when deciding filesystem and engine placement.

For an NVIDIA GPU, validate the supported Windows-driver-to-WSL path and container access. The Windows driver supplies the WSL GPU driver integration; do not install an ordinary Linux NVIDIA display/kernel driver inside WSL. Follow the current [NVIDIA CUDA on WSL guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) for the actual hardware and environment. Install only the runtime/tooling that the chosen container topology requires.

Check available WSL memory/swap and disk space before downloading weights. If resource configuration must change, record the exact change and its impact. Treat a WSL shutdown, machine reboot, driver replacement, or interruption of unrelated workloads as an explicit operational action rather than an invisible setup side effect.

Verify browser access from Windows to the API's published port. Document the actual URL and any required forwarding for the observed network mode; do not assume WSL addresses or forwarding behavior are identical across machines.

### Native Linux target

Use a supported Docker Engine/Compose installation and the GPU container integration appropriate to the observed hardware and selected model. Reuse a compatible existing setup. The application must not require Docker Desktop, Windows commands, drive-letter paths, WSL packages, or `/mnt/c` mounts.

Keep machine startup integration, filesystem ownership, device access, and service management in deployment scripts/configuration. If systemd is appropriate and available, provide an optional unit or documented startup procedure without making systemd an application dependency.

### Both targets

Use the same API, dispatcher, worker, broker, database, and storage contracts. Different host paths, runtime devices, ports, and limits are configuration values. If a hardware-specific worker image is necessary, isolate that difference in image/build selection, not in unrelated API/UI code.

Default to a local single-user deployment with the application host port bound to loopback. Keep the database, broker, and worker internal. LAN or internet access requires an explicit deployment scope and the corresponding access controls; do not widen exposure just to work around a local connection problem.

If a required privileged action or license/access decision cannot be completed with the available authorization, identify the precise missing action and continue independent preparation. Do not repeatedly ask for decisions already supplied by the user.

## 5. Prepare reproducible machine configuration

Create or adapt deployment files along these lines:

```text
deploy/
  compose/
    compose.production.yaml
    compose.gpu.yaml             # Only if a separate GPU override is useful
    compose.wsl.yaml             # Only for actual WSL-specific differences
    compose.linux.yaml           # Only for actual native-Linux differences
  env/
    deployment.env.example
scripts/
  deploy/
    preflight.sh
    start.sh
    stop.sh
    status.sh
    smoke-test.sh
    backup.sh
    restore.sh
    wsl-entry.ps1                # Optional thin Windows entry point
```

Avoid near-identical WSL and Linux Compose copies. Prefer one base configuration with small overrides only where differences are real. Any PowerShell wrapper must invoke the portable deployment entry point and handle argument/path quoting correctly; application services themselves must not call `wsl.exe`.

Provide documented configuration for:

- Deployment name, host bind address/port, and the URL the user should open.
- Database and broker credentials/URLs, internal service names, and connection limits.
- Persistent project/artifact storage and model-cache locations.
- Lyrics provider and music provider selection.
- Model identity, pinned revision, weights path, device, precision, duration limits, concurrency, and timeouts.
- Queue names/routing and mock versus real worker selection.
- Logging, restart policy, readiness, and graceful shutdown.
- Any vendor-specific cache variables required by the selected model runtime.

Keep actual secret files local and ignored by version control. Generate suitable deployment credentials rather than relying on broker/database example passwords. Do not bake access tokens into images, frontend bundles, build arguments that become image history, or committed manifests.

Preflight scripts must report missing prerequisites and invalid paths/configuration clearly. Validate the resolved Compose configuration, including profiles, mounted paths, user permissions, ports, and GPU device requests. Ensure only the intended worker can consume each kind of job.

Document the exact tested commands for mock start, real start, logs, status, stop, migrations, and provider switching. Re-running ordinary setup should preserve projects, artifacts, cache, and credentials. Keep data reset and volume deletion separate from normal stop/update commands.

## 6. Deploy and verify the mock stack on the target first

Before installing or debugging a real model:

1. Build or select the API image containing the compiled frontend.
2. Start persistent PostgreSQL and the durable broker using the intended deployment configuration.
3. Run the migrations once through the documented migration path.
4. Start the dispatcher, API, and mock worker.
5. Verify dependency health, service networking, storage permissions, and worker readiness.
6. Open the UI through the API's URL from the actual user-facing browser location.
7. Submit a brief with static or user-provided lyrics.
8. Confirm the queue/worker path, job persistence, artifact creation, playback, and seeking.
9. Save/reopen the project, create an iteration, and verify both versions remain available.
10. Restart services without deleting volumes and prove that the project and audio survive.

Record the tested URL, job/version identifiers, provider mode, and relevant logs/results without secrets. A reachable API documentation page or a green container list is not sufficient evidence of the application workflow.

If this phase fails, fix the application/environment boundary before introducing real-model dependencies. Keep the successfully tested mock profile available as a diagnostic mode after real inference is enabled.

## 7. Select, package, and activate the real model

### Establish a model that matches the host and product

Use an already specified model if it fits the target. If the repository does not identify one, evaluate a small number of plausible models using their official repositories/model cards and the observed hardware. Record the selection and reasoning in a model decision document.

For each serious candidate, determine:

- Exact repository/model identifier and revision.
- License and any download/access conditions relevant to deployment.
- Supported operating/runtime environment and accelerator requirements.
- Expected weight/download size, peak RAM/VRAM needs, and whether the claimed requirements are documented or estimated.
- Text-to-music, instrumental, vocal, exact supplied-lyrics, supported language, duration, and audio-conditioning capabilities.
- Available inference interface, dependency compatibility, and feasibility of packaging it inside the worker.
- Known limitations and how they affect the MuseForge controls and iteration behavior.

Do not assume that generating text lyrics plus instrumental audio produces a sung song. Do not claim language support, accurate lyric singing, three-minute output, editable stems, or precise audio editing without model evidence and appropriate testing.

Choose a practical model/configuration for the observed machine and document the tradeoff. If the only viable model has narrower capabilities than the product target, expose that limitation in the API/UI and keep the unmet target explicit. Do not silently redefine full product completion around an instrumental-only smoke test.

If no viable model can run on the available hardware, complete the host/mock deployment and record the exact missing requirement. Do not fabricate a working GPU path, secretly replace real inference with fixtures, or claim the real-model phase complete.

### Acquire and package weights reproducibly

Keep weights in a persistent model/cache location outside Git and outside the lightweight API image. Prefer pinned model revisions and verify downloaded content using available repository metadata/checksums. Support resuming or reusing valid downloads. Check available disk space before a large download.

Record model identity/revision, source, license reference, cache location, runtime versions, and image version in the deployment manifest. Do not commit authentication tokens. Separate the first model acquisition step from steady-state startup so repeated restarts do not unexpectedly download another revision.

If model files are gated or terms need a user decision, identify the specific outstanding access step. Continue preparing the image, configuration, and mock verification while that input is pending.

Use a separate real-worker image/build target with compatible, pinned Python, ML framework, audio tooling, and accelerator runtime dependencies. Choose versions based on the selected model and current official compatibility guidance; do not assume that the newest CUDA/runtime combination is appropriate.

Implement or finish the concrete provider adapter if it was explicitly deferred from Part 1. Keep that code in the portable provider/worker modules, add relevant contract tests, and update the application implementation records. Do not embed inference logic into a machine-specific shell script or the API service.

### Verify acceleration and model readiness in layers

For a supported GPU configuration, verify:

1. The host sees the intended GPU.
2. The selected WSL distribution sees it, if WSL is involved.
3. A container launched through the actual selected engine can access it.
4. The ML framework inside the actual worker image can allocate/use the intended device.
5. The selected model loads and performs a short inference within observed resource limits.

Use the appropriate vendor procedure. For Docker Compose GPU configuration, consult [Docker's GPU service documentation](https://docs.docker.com/compose/how-tos/gpu-support/) and verify the prerequisites and resolved device reservation on this host. Do not treat a successful host GPU command as proof that the worker can use the GPU.

Use CPU inference only when the selected model supports it and the resource/latency implications are acceptable and documented. A mock CPU profile must remain available even when real CPU inference is impractical.

### Run the model through the actual application worker

Load and warm the model inside the inference worker process. Mark real-worker readiness only when required weights and dependencies are available and the model is ready to serve jobs. Keep API liveness independent of model warm-up.

Start conservatively with one active inference per GPU worker, compatible process-pool behavior, low prefetch, and bounded queue/retry behavior. Select precision and duration limits based on the actual model/device, not guessed VRAM capacity. Ensure heartbeats and cooperative cancellation remain responsive during a long inference call.

Persist model ID/revision, relevant inference settings, seed when applicable, measured duration, and provider identity with the job/version. Reject unsupported options clearly. Never silently switch a real request to mock output, another model, or a shorter duration without reporting the effective behavior.

Validate output files before success: decodability, non-empty audio, measured duration, sample rate/channel metadata, content type, and artifact persistence. Mark any estimated song structure honestly. Keep lyric text and actual audio-conditioning support separate in result metadata.

## 8. Validate the real deployed workflow and recovery

Run browser and API checks against the deployed application, not only a standalone model command. Begin with a short generation within the model's supported limits, then test a representative request appropriate to the machine.

Verify:

- The browser UI is served by the API; nested routes refresh correctly and assets load after an image rebuild.
- Real-mode capabilities and readiness appear accurately; no mock worker accidentally handles the real request.
- Job submission returns promptly while inference runs asynchronously through the broker.
- Lyrics supplied by the user remain intact, with any limits on singing those lyrics clearly shown.
- The model produces actual audio, the API serves it, and browser play/pause/seek/download work.
- Job metadata identifies the actual model/revision; the result does not reuse a mock artifact by mistake.
- An iteration/regeneration creates a new version, retains the parent, and preserves earlier audio. Test only refinement semantics the provider actually supports and document fallbacks such as full regeneration.
- Project/version/artifact state survives browser refresh, API restart, and an ordinary full stack restart.
- Queued cancellation, running cancellation behavior, bounded retry, and worker loss result in coherent visible job states.
- Broker/API/dispatcher interruptions do not permanently strand accepted work or duplicate completed versions.
- Disk/permission failures and model initialization/resource errors produce actionable errors rather than false success.

Run disruptive recovery checks with dedicated test jobs and data. Do not destroy the user's existing library to prove recovery behavior. Use the mock profile for repeatable fault injection where a real GPU failure would add no useful evidence, and identify which checks used which provider.

Record cold model-load time, warm generation time, queue wait, actual audio duration, observed CPU/RAM/VRAM use, and any practical concurrency limits. Distinguish measurements from estimates and cold starts from warm requests. Do not promise throughput or reproducibility across hardware based on one sample.

If listening tools are available, check audible playback; otherwise report technical audio validation and leave subjective musical quality unverified. A valid audio container alone does not prove that the generated song follows its brief or sings the supplied lyrics correctly.

## 9. Provide an operational runbook and portability evidence

Write a runbook with exact, tested steps for:

- Starting, stopping, checking health, opening the app, and viewing correlated logs.
- Selecting mock or real providers without rebuilding unrelated UI/API code.
- Diagnosing model warm-up, unavailable GPU, memory exhaustion, stuck jobs, inaccessible artifacts, full disks, and broker/database connection failures.
- Gracefully draining/stopping workers and understanding what happens to queued and running jobs.
- Restarting after a host reboot or WSL shutdown, including the chosen engine's startup requirements.
- Updating application images, running migrations once, preserving local configuration, and checking the deployed revision.
- Pinning/updating model revisions deliberately, without invalidating old version metadata.
- Backing up PostgreSQL plus the referenced artifact set and necessary configuration metadata.
- Restoring into an isolated target and verifying that restored projects can play their audio.
- Rolling back application/model changes, with database compatibility considered explicitly.

Define a consistent backup boundary: quiesce relevant writes or use a documented coordination method so the database and artifact backup describe the same usable state. Model weights may be restored from cache or reacquired at the recorded revision. Account for queued/running jobs and reconcile them rather than blindly replaying stale task messages after restoring an older database.

Do not treat copying a live PostgreSQL data directory as a verified logical backup. Use a supported database backup approach and prove at least one restore against separate test storage. Keep ordinary stop/upgrade procedures free of volume deletion. If a migration is not safely reversible, document the tested backup/restore recovery path instead of assuming that a downgrade command is sufficient.

Create a deployment manifest containing:

- Machine alias, OS/WSL topology, and validation date.
- Application commit/revision or equivalent source fingerprint and image identifiers.
- Active Compose files/profiles and non-secret effective settings.
- Application URL and internal/external port mapping.
- Data, artifact, and model-cache locations and ownership expectations.
- Model identifier/revision, license reference, runtime/device/precision, and measured safe limits.
- Status of the mock and real smoke tests.
- Any known limitations and links to phase reports and verification evidence.

In `portability-matrix.md`, distinguish `verified on host`, `configuration checked`, `documented only`, and `blocked` for WSL and native Linux. If only a WSL host is available, validate the native-Linux configuration and remove Windows dependencies, but do not claim an actual native-Linux deployment occurred. Apply the same honesty in the opposite direction.

## 10. Suggested deployment phases

| Phase | Work | Exit criteria |
| --- | --- | --- |
| D00: Inventory and plan | Audit implementation, inspect host, choose topology, write all phase plans/status/to-do files | Target, resources, model decision process, dependency gaps, and acceptance checks are explicit |
| D01: Host preparation | Prepare selected engine/runtime, directories, permissions, configuration, and device access | Required services can run; configuration validates; device/container checks required for the selected target pass |
| D02: Mock deployment | Start the packaged application with actual DB/broker/worker and mock inference | Browser-to-worker generation, playback, versioning, persistence, and restart work on the target machine |
| D03: Real model | Select/verify model, acquire pinned weights, finish adapter/image, load and run it through the queue | At least one real queued application job produces a persisted playable result with accurate model metadata |
| D04: System validation | Browser flow, supported iteration, reliability/recovery checks, representative resource measurement | Required real workflow and relevant recovery criteria pass with recorded evidence and truthful capability limits |
| D05: Operations and handoff | Runbook, deployment manifest, backup/restore check, startup/update/recovery instructions, portability matrix | The user can operate and reproduce the deployment; completed phases have implementation-status.md reports |

You may refine this sequence based on the inventory. Keep mock deployment ahead of real-model debugging. A phase with a failed required exit criterion stays open even if substantial work is finished. Continue independent phases/tasks where their dependencies permit, and record the blocker precisely.

## 11. First response and final handoff

Your first response must summarize the repository's deployment readiness, observed target environment, chosen or proposed topology, missing critical facts, and phase plan. Write the detailed Markdown plan before changing deployment state.

At the end, report:

1. What was deployed and the exact application URL.
2. Whether the active music provider is real or mock, which model/revision is in use, and what it can actually do.
3. Which end-to-end and recovery checks passed, and any checks not run.
4. The exact tested start/stop/status commands and locations of data/model cache.
5. Links to the machine runbook, manifest, verification record, and phase implementation reports.
6. Remaining limitations or blockers, including any unverified native-Linux or WSL deployment path.

Only declare real-model deployment complete after a request from the actual application has passed through the queue and worker, produced real model audio, persisted its result, and been retrieved through the API for playback. Starting containers or successfully importing an ML library is not sufficient.
