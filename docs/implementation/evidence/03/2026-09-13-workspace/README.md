# Phase 03 responsive workspace evidence

Run started 2026-09-13 and completed 2026-09-14. The compiled UI was served by FastAPI on the existing Docker VM at `<verification-host-address>`, reached through a loopback SSH tunnel. No Vite server, HTTP request stubs, eager Celery or SQLite supplied the integrated result. The mock worker, PostgreSQL and RabbitMQ ran as separate containers. The original isolated runner used project `museforge-phase2-test`; browser verification used the separate `museforge-phase3-browser` project.

## Results and reproduction

- [Python unit results](python-unit.txt): 97 passed. The container equivalent passed 96 with the existing Git-only skip.
- [Frontend build and unit results](web.txt): TypeScript/Vite build and 3 Vitest tests passed. Container images used the pinned Node/npm stages; the local Node runtime was 24.14.1.
- [Real-service integration](integration.txt): 29 passed, including all four iteration operations, exact lyrics, source parentage, reused audio identity, conditional project/version revisions, cross-project selection rejection, and manual selection surviving completion.
- [Final lineage check](lineage-final.txt): 5 passed after adding the favorite-list assertion.
- [Browser suite](browser.txt): 25 passed at 1440, 390, 360 and 320 px; three duplicate desktop-only behavior cases intentionally skipped in the mobile projects. Actual playback, seek, download, refresh, source equality, iteration history, favorite/rename, responsive bounds and axe passed.
- [Final workspace checks](workspace-font-check.txt) reran the responsive workspace after bundled fonts: eight passed and the final 320 px case hit an artifact-directory collision between two concurrent Playwright invocations, not an application assertion. [Isolated 320 px rerun](narrow-final.txt) passed with a separate output directory. Future parallel CLI runs must use distinct `--output` paths.
- [Cancellation and stale save](recovery-browser.txt): cancellation, deliberate regeneration, a real 412 conflict, preserved local text and reviewed resave passed.
- [Queued restart checkpoint](queued-restart.json): the Phase 02 idempotent queued/API-restart path still passed, followed by real smoke/playable artifact checks.

Commands: `.venv/bin/python -m pytest tests/unit -q`; `npm run build && npm test` in `apps/web`; `python3 scripts/verify-phase2.py` on the isolated VM checkout; `API_BASE_URL=http://127.0.0.1:18033 npm run test:browser`; targeted `playwright test browser/workspace.spec.ts`; and `API_BASE_URL=http://127.0.0.1:18033 node scripts/verify-workspace-browser.mjs`. The last script creates dedicated original test content and captures native Chromium zoom using a temporary local extension calling `chrome.tabs.setZoom(2)`. It deletes that extension after use. Screenshot capture at native zoom uses CDP to avoid Playwright viewport overrides.

## Visual and keyboard inspection

Inspected the supplied desktop/mobile references and these API-served captures: [1440 px](workspace-1440.png), [390 px](workspace-390.png), [360 px](workspace-360.png), [320 px](workspace-320.png), [native-script lyrics](native-script-lyrics.png), and [native 200% zoom](zoom-200-percent.png).

[Observations](observations.json) record DOM/visual order, scroll bounds at nine widths, one audio element across breakpoints, actual clipboard equality, reduced-motion media state, focus sequence and loaded glyph fonts. At native 200% zoom, a 1440 px browser window has a 720 px CSS viewport and devicePixelRatio 2; scrollWidth remains 720 and Rename version is above the fixed navigation. All recorded interactive keyboard stops have a visible solid outline. Radio groups provide one Tab stop and native arrow navigation; the disabled unsupported vocal selector is skipped. The focus sequence follows desktop lyrics-before-player order and the narrow layout has player-before-lyrics DOM order. These are Chromium visual/keyboard inspections, not a claim of screen-reader certification or other-browser release coverage.

The font check identified missing rendered Tamil glyphs in the initial system fallback. Licensed local Noto Sans Tamil, Devanagari and Gurmukhi fonts now ship as hashed Vite assets. CDP confirms the final Tamil and Devanagari glyphs use bundled custom fonts, and the final lyric crop is readable. Original whitespace/native text remains exact. [Contrast calculations](contrast.json) give body 13.88:1, supporting text 6.00:1, primary button labels 5.96:1, control boundaries 3.80:1, focus 5.70:1 and errors 7.42:1.

## Working control inventory and tradeoffs

| Surface | Working behavior |
| --- | --- |
| Navigation | Create and Projects open real destinations; project links reopen saved state. |
| Composer | Code-point brief counter/validation, original examples, all instrument/mood/language choices, genre/tempo, lyrics source/editor, duration/seed. Unsupported vocals are explained and disabled. |
| Save | Server title/draft save with If-Match; separate local/unsaved/saving/saved/failed feedback and local/server recovery choices. |
| Job status | Authoritative stage/attempt/dispatch/readiness, cancellation, completion/failure, preserved draft and deliberate Generate again. Polling backs off to 10 seconds and reconnect refreshes state. |
| Player | One audio element; measured seek/time, play/pause, volume, WAV download, previous/next, shuffled project collection, repeat off/one/collection. Repeat collection continues only already requested playback; selection/completion never starts playback by itself. |
| Lyrics | Read-only selectable output, confirmed clipboard or failure fallback, explicit edit/apply/cancel; lyrics-only child versions disclose Audio unchanged. |
| Iterate | Apply Changes, targeted mood/instruments, Regenerate and Create Variation submit real jobs with exact instruction and parentage. Background completion preserves a manual selection. |
| History | Complete paginated version collection, conditional selected version, label/favorite metadata, actual counts and parent context. |
| Structure | Honest unavailable state and actual artifact duration; no invented section timing or waveform. |

The 1440 px rail is 224 px and composer 448 px; 1200–1399 px uses the compact 72 px rail. Narrow musical fields reflow below 360 px. Vertical scrolling is intentional. Buttons use solid blue for contrast. Playback uses a measured seek slider rather than a synthetic waveform. Font fallback is bundled for the supported Indic scripts. Large decoration and artwork are omitted. Iterate uses a full-width text field/button for instruction readability. These are documented design tradeoffs, not missing audio semantics.

Library, Settings, Templates, duplicate/archive and full multi-tab/offline reconciliation remain Phase 04. No placeholder navigation for them is presented. The mock provider does not sing lyrics or understand precise semantic audio edits; no real model or Part 2 deployment is claimed. Partial lyrics are not exposed because the current capabilities do not offer a partial browser result.
