# Phase 03 to-do

All items are implementation work and remain unchecked. Planning preparation is tracked in Phase 00.

- [ ] 03-01 Implement shared visual tokens, typography, outline icons, brand, cards/chips and responsive AppShell/Composer/Result components from ui-behavior.md. Apply the documented 1440 px column/rail adjustment and 320–360 px field reflow.
- [ ] 03-02 Complete the brief counter/validation, all instrument/mood/language choices, Genre/Tempo/Vocal Type and capability-aware Advanced Options. Provide source selection and accessible user lyrics editor, with original examples and unchanged submitted text.
- [ ] 03-03 Build the HTML audio controller and accessible seek control, elapsed/measured total time, play/pause/volume/download, repeat and the project-version playback collection for previous/next/shuffle. No autoplay; derive any displayed waveform peaks from decoded audio.
- [ ] 03-04 Implement PATCH project active selection/draft/title and PATCH version label/favorite metadata with revision checks. Add working favorite/rename controls and load complete version detail atomically for preview/lyrics/structure/iteration context.
- [ ] 03-05 Implement POST version iterations for regenerate/refine/variation/lyrics_edit using the same idempotent outbox job path. Persist parent, instruction and exact inputs; a lyrics-only version reuses the audio with an explicit Audio unchanged disclosure.
- [ ] 03-06 Build read-only result lyrics, clipboard confirmation/failure path and explicit Refine Lyrics edit mode. Render only valid measured/estimated song structure within actual duration and provide mobile disclosure.
- [ ] 03-07 Wire Iterate/Apply Changes, targeted mood/instrument editing, Regenerate and Create Variation to real endpoints. Show conservative mock-action explanation; preserve every previous version and report background completion without replacing manual selection.
- [ ] 03-08 Implement local IndexedDB draft/base-revision persistence, basic saved/saving/error feedback, bounded polling/reconnect indicators and all applicable empty/queued/running/partial/complete/error/cancel states. Full multi-tab reconciliation is Phase 04.
- [ ] 03-09 Implement desktop/mobile semantic reading order with one active player state, safe bottom navigation, named menus, visible focus, radio/pressed semantics, live-region announcements, touch targets and reduced-motion/zoom handling.
- [ ] 03-10 Run component/type, API iteration/selection and Playwright/axe checks at 1440, 390, 360 and 320 px plus breakpoint checks; manually inspect keyboard order, contrast, long native-script lyrics, no-overflow and safe fixed actions at 200% zoom.
- [ ] 03-11 Document visual/capability tradeoffs and working control inventory, refresh development/API docs and phase tracking, and create implementation-status.md only after all exposed workspace actions and responsive acceptance criteria pass.

No task has been removed or moved. If scope changes, keep the original identifier, explain the change and link its destination. See [plan](plan.md) and [status](status.md).
