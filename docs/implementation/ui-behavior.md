# Responsive workspace and interaction decisions

- Date: 2026-09-13
- State: planned; visual and browser acceptance has not run
- Sources: [design](../../design.md), [desktop mockup](../ui%20mockups/mockup_desktop.png), [mobile mockup](../ui%20mockups/mockup_mobile.png)
- Implementation: basic composer in 02, full workspace in 03, organization/recovery in 04, capability audit in 05

## Visual reference findings and tradeoffs

Both images were inspected. The desktop reference establishes the left navigation, composer card, lyrics/player pair, structure, iteration controls and version cards. The mobile reference establishes one column, preview before lyrics, full-width generation/refinement, and fixed bottom navigation. It depicts a device frame and a subset of choices; neither belongs in the actual page implementation.

The written desktop minimum is `256 + 40 + 520 + 16 + 680 = 1512 px`, so literal minimums overflow at the required 1440 px. Adopt this responsive sizing and verify it rather than shrinking text or targets:

| Width | Navigation and workspace rule |
| --- | --- |
| 320–359 px | One column; 16 px side padding; two-column Genre/Tempo with Vocal Type full width; cards can reduce padding to 12 px |
| 360–767 px | One column; 16 px side padding; around 390 px use three musical fields with Tempo widest; wrap chips; fixed safe-area-aware bottom navigation |
| 768–1199 px | Single workspace column by default; collapsible navigation; preserve readable controls and full-width result sections |
| 1200–1399 px | Compact 72 px navigation rail with named/tooltipped controls; two main columns starting at 400 px composer and flexible result |
| 1400–1599 px | 224 px rail, 20 px workspace padding, 16 px gap; 448 px composer and flexible results; at 1440 px result space is 712 px |
| 1600 px and wider | 256 px rail; composer 520–560 px (up to 580 at very wide sizes); result flexes; centered content maximum 1680 px |

Use `min-width: 0` on flexible content and wrap or clamp long metadata. Within results, lyrics/player may share columns when result width is at least 640 px; otherwise stack. All required sections remain in the page with vertical scrolling allowed; there must be no horizontal page scrolling. Horizontal scroll belongs only to labelled structure/action/version collections.

Keep one shared source of player/version state. Render semantic card order for the active layout: desktop lyrics then preview; mobile composer, preview, lyrics, Iterate, structure/history. Only one instance of each interactive card is active. Preserve audio controller/selection when switching breakpoints; do not duplicate a playing audio element or use CSS ordering that contradicts keyboard order.

Use the specified blue/navy/neutral tokens, font stack, 4–40 px spacing scale, 14–16 px cards, 10–12 px inputs and 10 px chip corners. The mobile image's pill shapes yield to the written chip specification. Primary text/action contrast must meet the written AA targets; use a tested solid brand-blue button if the optional light-blue gradient fails white-label contrast. Consistent rounded outline icons and simple original waveform branding suffice; decorative waterfront art is optional. The image's artwork/lyrics/title/duration are reference content, not a license or runtime fixture requirement.

## Routes and navigation

Create is `/create` (also entry `/`); a persisted workspace is `/projects/{id}`. Library `/library`, Projects `/projects`, Settings `/settings`, and Templates `/templates` are real routes when delivered. Desktop shows the rail/top bar; mobile shows Create/Library/Projects/Settings bottom navigation, with Templates and Advanced Options in accessible menus. Search is a Library function; desktop utility search routes to it once Phase 04 implements it. No fake account, notifications, upgrade or collaboration controls are displayed.

At Phase 03, show only destinations/actions whose endpoints are implemented; Phase 04 adds all remaining required local navigation and organization flows. Omitted future controls are tracked work, not completion of those features. Results/Versions use actual counts and explicit current selection. Mobile structure/history are accessible collapsible sections below Iterate; focused actions wrap or scroll within their own container.

## Composer and lyrics modes

Use the full vocabulary and bounds in [contracts](contracts.md). Brief textarea has an exact live 500-code-point counter, associated error/help text and preserved content. Try an example fills a complete valid brief without generating; examples span languages and moods using original text. Instruments are multi-select with `aria-pressed`; mood/language are radio groups. Show all options on narrow devices using wrapping.

Lyrics source is a visible user/static/mock selector. User mode exposes an accessible editor and preserves Unicode, stanza labels, whitespace and line breaks exactly as submitted. Static and mock lyrics are labelled. Result lyrics are read-only by default; Refine Lyrics opens an explicit editor with Apply/Cancel, and Apply creates another version. Copy reports success only after clipboard success and exposes a safe selectable-text fallback on failure.

Generate is at least 56 px high desktop / 58 px mobile and disabled for invalid brief/required selections. Show unavailable provider capability explanations near relevant fields. Defaults remain sufficient: Indie Pop, Medium tempo and mock Instrumental; unsupported Male/Female/Mixed Vocals remain explained product options. Advanced Options exposes supported duration and seed plus effective provider information; hide unsupported key/time-signature/quality/balance features rather than imply they work.

## Player, results, and meaningful actions

Drive playback from the returned artifact URL using one HTML audio controller. Implement play/pause, keyboard/touch seeking, measured elapsed/duration, volume, repeat and download. Prefer an accessible seek slider as the first waveform equivalent. If showing a waveform later, derive peaks from decoded audio; decorative marks carry no measured-data claim. Never autoplay on completion, navigation or version selection.

Previous/next/shuffle operate on the selected project's completed playable versions in version-number order, captured as the current collection. Selecting a library item establishes that item's project collection. Shuffle permutes that collection for the current playback session; a one-item collection disables previous/next/shuffle with named explanations. Repeat cycles off/one/collection and persists the local preference when settings land. Never skip silently over missing artifacts: show which item is unavailable and allow a deliberate next action.

Favorite and rename call the organization endpoints and show failures without losing state. Duplicate/Archive arrive with Phase 04 and use the explicit project-level semantics in contracts. Downloads return the original available WAV format; unsupported export formats are not offered. Track title/duration/artwork/version count come from actual records; fallback artwork is an original local placeholder, not fabricated album provenance.

Structure uses actual measured metadata or clearly labelled estimates within audio duration. Initial absence shows Structure unavailable. Use text plus the specified pale blue/green/orange sections; sections may support seeking only when valid timing exists. Never stamp the example 3:24 timeline onto the default 8-second demo.

Free-text Apply Changes preserves the instruction and submits a new job from the source version. In mock mode explain that another demo is produced and precise semantic audio changes are not supported. Regenerate starts from preserved/visibly edited inputs; Change Mood and Try New Instruments open targeted draft controls; Create Variation records the selected parent. Refine Lyrics may reuse audio and must say Audio unchanged. No credit confirmation is needed for free local mock generation; a future paid provider would introduce its own cost policy.

Switching version updates audio, lyrics, structure and iteration source together, resets play position without autoplay, and never deletes later versions. Announce a background result without switching away from a later manual selection. Titles/labels remain editable metadata; generated content is immutable.

## Job, save, and network states

| State | Observable response |
| --- | --- |
| Empty/ready | Concise result guidance; Generate becomes enabled only when inputs validate |
| Queued | Preserve submitted and unsent draft separately; show backend status/worker availability; allow cancellation |
| Running | Stage label and indeterminate progress unless meaningful percentage exists; persisted cancel command |
| Partial lyrics | Only if a durable lyrics checkpoint exists and the capability supports partial results; audio remains explicitly pending |
| Complete | Reveal and politely announce result; offer focus/scroll when appropriate without moving focus while user is editing |
| Failed/timed out | Safe actionable error, attempt/retry status and preserved inputs/prior results; Retry creates a linked job |
| Cancellation requested/cancelled | Distinct labels; explain any delay in stopping computation; never show discarded audio as a successful version |
| Offline/reconnecting | Disable server mutations, retain local drafts and cached view, show status; backoff polling and reconcile on reconnect |
| Saving/saved/save failed | Inline confirmation/error; never claim remote save based only on local autosave; revision-conflict choices preserve both edits |

Start polling around 1 second, back off up to 10 seconds on failures, reduce work for hidden tabs, stop terminal polling, and fetch fresh state on reconnect. Avoid queued duplicate submissions with persisted idempotency intent. Saving uses revision checks; multi-tab conflicts never silently replace server or local drafts.

## Accessibility and visual acceptance

Meet the specification's contrast thresholds (4.5:1 normal text, 3:1 large text/UI boundaries); test actual selected/focus/error states. Minimum target 44×44 px, playback at least 48×48 px. All icon buttons have accessible names and pointer tooltips. Provide logical tab order, visible 2 px focus rings, no keyboard traps, polite progress/completion live regions and assertive actionable errors. Text and icons supplement color.

Test keyboard-only composer -> submit -> cancel/retry -> playback seek -> lyrics edit -> iteration -> history -> Save. Respect reduced motion and keep transitions below 200 ms. At 200% zoom/large text, fixed bottom navigation and safe-area spacing cannot hide the final interactive content. Avoid truncating native-script lyrics and long labels. No scroll-jacking on progress or unexpected focus movement.

Phase 03 captures screenshots at 1440, 390, 360 and 320 px and checks 768, 1199, 1200 and 1600 px boundaries. Use `scrollWidth <= clientWidth` checks for page overflow and keyboard/manual inspection alongside axe; automated accessibility scans alone do not establish complete AA conformance. Phase 04 repeats changed flows for offline/reconnect, empty library, long content, settings and save conflicts. Phase 06 records final API-served browser evidence.
