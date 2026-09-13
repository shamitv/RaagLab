# Phase 03: Complete responsive workspace

## Objective

The integrated mock flow becomes the designed desktop/mobile creative workspace: users can control playback, edit lyrics explicitly, refine or branch a result and switch versions without losing context, with accessible controls and honest demo behavior.

## Dependencies and entry criteria

Phase 02's API-served browser-to-worker checkpoint passes and is recorded. Use design.md, both inspected mockups, ui-behavior.md and the existing typed contracts. Existing integration must stay functional while components are refactored.

## Scope

App shell, composer controls, advanced options, full player, lyrics display/editor, estimated/available structure, iteration/focused actions and version history. Implement the small metadata/selection/iteration endpoints required by these controls in this phase. Library duplication/archive/settings/template management and full offline/save reconciliation complete in Phase 04; expose only working destinations/actions until then.

## Work breakdown

1. **03-01** Implement shared visual tokens, typography, outline icons, brand, cards/chips and responsive AppShell/Composer/Result components from ui-behavior.md. Apply the documented 1440 px column/rail adjustment and 320–360 px field reflow.
2. **03-02** Complete the brief counter/validation, all instrument/mood/language choices, Genre/Tempo/Vocal Type and capability-aware Advanced Options. Provide source selection and accessible user lyrics editor, with original examples and unchanged submitted text.
3. **03-03** Build the HTML audio controller and accessible seek control, elapsed/measured total time, play/pause/volume/download, repeat and the project-version playback collection for previous/next/shuffle. No autoplay; derive any displayed waveform peaks from decoded audio.
4. **03-04** Implement PATCH project active selection/draft/title and PATCH version label/favorite metadata with revision checks. Add working favorite/rename controls and load complete version detail atomically for preview/lyrics/structure/iteration context.
5. **03-05** Implement POST version iterations for regenerate/refine/variation/lyrics_edit using the same idempotent outbox job path. Persist parent, instruction and exact inputs; a lyrics-only version reuses the audio with an explicit Audio unchanged disclosure.
6. **03-06** Build read-only result lyrics, clipboard confirmation/failure path and explicit Refine Lyrics edit mode. Render only valid measured/estimated song structure within actual duration and provide mobile disclosure.
7. **03-07** Wire Iterate/Apply Changes, targeted mood/instrument editing, Regenerate and Create Variation to real endpoints. Show conservative mock-action explanation; preserve every previous version and report background completion without replacing manual selection.
8. **03-08** Implement local IndexedDB draft/base-revision persistence, basic saved/saving/error feedback, bounded polling/reconnect indicators and all applicable empty/queued/running/partial/complete/error/cancel states. Full multi-tab reconciliation is Phase 04.
9. **03-09** Implement desktop/mobile semantic reading order with one active player state, safe bottom navigation, named menus, visible focus, radio/pressed semantics, live-region announcements, touch targets and reduced-motion/zoom handling.
10. **03-10** Run component/type, API iteration/selection and Playwright/axe checks at 1440, 390, 360 and 320 px plus breakpoint checks; manually inspect keyboard order, contrast, long native-script lyrics, no-overflow and safe fixed actions at 200% zoom.
11. **03-11** Document visual/capability tradeoffs and working control inventory, refresh development/API docs and phase tracking, and create implementation-status.md only after all exposed workspace actions and responsive acceptance criteria pass.

## Contracts and data changes

Add iteration and metadata/selection endpoints and conditional revision handling according to ../../contracts.md. Content fields remain immutable; organizational patches cannot rewrite lyrics/audio. Favorite is a version-level relation. All job-producing actions reuse the Phase 02 immutable snapshot/outbox/claim pipeline. Structure distinguishes measured/estimated/unavailable, lyrics-only output declares audio_recomposed=false and playback uses actual artifact metadata.

## Acceptance criteria

- **03-AC1:** 1440 px has visible navigation/composer/results/structure/iteration/history with no horizontal page scroll; 390 px is one column with full-width Generate/Apply and safe bottom navigation; 320/360 px remain usable.
- **03-AC2:** All exposed composer/advanced controls validate consistently with the API, preserve inputs and explain unsupported model features without claiming vocal or semantic demo output.
- **03-AC3:** Real audio plays, pauses, seeks and downloads via the API; collection/repeat controls behave as documented or are disabled when inapplicable; no unexpected autoplay occurs.
- **03-AC4:** Copy/edit lyrics, favorite/rename, each focused iteration action, parentage and version selection perform their actual API actions; earlier results survive and panels update together.
- **03-AC5:** Empty, pending, completion, error, cancellation and reconnect presentations use authoritative data and actual metadata, with no hard-coded reference duration or version count.
- **03-AC6:** Keyboard, named icons, focus, chips, progress announcements, contrast, target sizes, reduced motion and 200% zoom/fixed navigation checks pass at required widths with manual evidence.
- **03-AC7:** Browser acceptance uses the compiled UI served by the API and preserves the Phase 02 integrated checkpoint.

## Verification

Planned: bash scripts/test.sh unit (frontend types/Vitest plus affected contracts); bash scripts/test.sh integration for test_version_lineage.py and conditional metadata/selection; bash scripts/test.sh e2e with player.spec.ts, lyrics.spec.ts, iterations.spec.ts, responsive.spec.ts and accessibility.spec.ts. Capture API-served state screenshots and manual keyboard/zoom/contrast observations under docs/implementation/evidence/03/<run-id>/. Assert measured playback time, source lyric equality, parent IDs and page scrollWidth bounds rather than only screenshot similarity.

## Risks, assumptions, and deferred work

Literal fixed desktop minima overflow at 1440 px; implement the recorded responsive adjustment. Browser audio and clipboard APIs differ, so failures must be visible and accessible. Mock refinement does not understand exact audio edits. Library/templates/settings/duplicate/archive and exhaustive save/offline/concurrency recovery remain Phase 04; those controls are not presented as working placeholders.

See the [master plan](../../master-plan.md), [requirement matrix](../../requirements-matrix.md), [status](status.md) and [to-do list](todo.md).
