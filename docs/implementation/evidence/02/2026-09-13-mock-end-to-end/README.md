# Phase 02 integrated checkpoint

The playable mock generation checkpoint passed on 2026-09-13. This is real HTTP → PostgreSQL/outbox → RabbitMQ → separate CPU worker → validated WAV → browser playback. No eager tasks, browser transport stubs, model weights, GPU, or paid endpoint were used.

## Environment and commands

The isolated Linux Docker VM was `10.42.0.42`; the browser used an SSH tunnel to the loopback-only API port. See [runtime inventory](runtime.json). Frozen container builds used Python 3.13.15, Node 24.21.0, and npm 11.19.0. Local frontend checks used Node 24.14.1/npm 11.11.0 with the same frozen package lock.

- `bash scripts/test.sh integration`: passed the complete isolated build/unit/integration/restart/smoke runner. Its generated project was `museforge-phase2-test-9e5d486ce410`; cleanup removed only that project's containers and volumes.
- `.venv/bin/python -m pytest tests/unit -q`: [97 passed locally](phase2-unit-local.txt). The container run had [96 passed and one expected Git-only skip](container-unit.txt); the checkout regression passed on the authoring host.
- `npm run build` and `npm test`: typecheck/build passed and [2 frontend tests passed](phase2-web-unit.txt). The final public error-schema correction passed [targeted contract checks](final-contract-check.txt), generated TypeScript, and a rebuilt API image.
- Real-service integration: [24 passed](integration.txt), including exact lyrics, scoped concurrent idempotency, duplicate delivery, isolation, failure/timeout/bounded retry, queued/running cancellation, range/HEAD/410, stale fences, selection sequencing, expired publication claims, expired execution leases, checkpoint reuse, and configured-default replay.
- `API_BASE_URL=http://127.0.0.1:18002 npm run test:browser`: [12 passed](phase2-browser.txt), with actual generation in all lyrics modes and desktop/mobile/narrow viewports. Playback time advanced; pause, seek, download, exact DOM lyric text, unsent edits, refresh, no overflow and axe checks passed.
- `bash scripts/seed-demo.sh`: [three source-labelled demos passed](seed-demo.json). The smoke client captured [decoded media](smoke-decoded.json): non-silent 5-second, 44.1 kHz stereo, 16-bit PCM; 220,500 frames, matching byte count and SHA-256.

## Persistence and correlation

With a dedicated worker stopped, acceptance took **0.025 seconds**. The same queued job survived an independent API restart and idempotent replay, then completed in one attempt after the worker resumed. See [queued restart record](queued-restart.json) and [19 preserved projects](restart.json). The harness rediscovers Docker's ephemeral host port after restart; this run changed 32776 to 32777.

A separate real browser refreshed and played the same saved audio/lyrics after restarting the API: [assertions](browser-api-restart.json), [trace](browser-api-restart-trace.zip), and [screenshot](browser-after-api-restart.png).

[PostgreSQL assertions](postgresql-assertions.json) found 53 succeeded jobs, 53 completed versions and 53 artifacts in the browser checkpoint stack, with zero duplicate job results, zero versions for non-successful jobs, and zero successful jobs without a result. This stack accumulated several test runs; its counts are distinct from the fresh runner's 19-project restart check.

The [generation browser trace](browser-desktop-trace.zip) contains accepted job identities and actual network/media responses. Match those IDs with [worker/dispatcher correlation](browser-worker-correlation.log). Screenshots: [desktop](browser-desktop.png), [mobile](browser-mobile.png), [narrow](browser-narrow.png). [Source hashes](source-sha256.json) identify the final implementation and test files.

## Corrections and limits

Initial checks found and corrected form contrast, obsolete foundation expectations, and a range-header test expectation. Artifact reads now open stored path components without following symlinks. Public error responses have matching OpenAPI types. Running two stacks concurrently overloaded the VM enough to expire process probes; final service verification ran sequentially and the readiness test waits for a fresh bounded observation. The restart harness initially retained Docker's old ephemeral port; it now rediscovers the mapping.

The audio is an original instrumental demonstration, not faithful musical conditioning or sung lyrics. Full visual work, revision-aware IndexedDB drafts, explicit retry/iterations, library/settings, exhaustive adversarial races and guarded orphan GC remain in their assigned later phases. The initial schema was sufficient and was not rewritten.
