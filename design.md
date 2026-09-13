# MuseForge AI — Product Design Specification

Status: UI implementation reference  
Platforms: Responsive web (desktop and mobile)  
Visual direction: Light mode, blue-led palette, minimal violet  
Reference screens: `MuseForge AI Music Dashboard.png` and `MuseForge AI Music App Mockup.png`

## 1. Product intent

MuseForge AI turns a natural-language song idea into editable lyrics and a playable music result. A user chooses instruments, mood, language, genre, tempo, and vocal type; generates a song; then iterates through natural-language changes or focused actions without losing earlier versions.

The experience should feel creative but precise: spacious white surfaces, confident blue actions, fast audio feedback, and obvious paths to refine or branch a result.

## 2. Core experience

1. Describe the song in **Song Brief**.
2. Select one or more instruments, one mood, and one language.
3. Choose genre, tempo, and vocal type.
4. Select **Generate Lyrics + Music**.
5. Review the generated lyrics, listen to the music, and inspect the song structure.
6. Enter an iteration request or use a focused refinement action.
7. Apply the change as a new version; keep every prior version available.
8. Save the project or create a variation.

## 3. Design principles

- **Creation first:** The brief and Generate action are the visual starting point.
- **Audio is the proof:** Once a result exists, Music Preview is the primary result card.
- **Iteration is non-destructive:** Every applied change creates a new version.
- **Progressive disclosure:** Keep common controls visible; place model and production details under Advanced Options.
- **Blue, not violet:** Use saturated blue for selection and action. Violet is not a primary brand or interface color.
- **Consistent hierarchy:** Use the same control labels, icons, selection state, and card language on desktop and mobile.

## 4. Information architecture

### Primary navigation

| Destination | Purpose | Desktop | Mobile |
| --- | --- | --- | --- |
| Create | Generate and refine songs | Selected item in left rail | Selected item in bottom navigation |
| Library | Browse generated and saved songs | Left rail | Bottom navigation |
| Projects | Organize related songs and versions | Left rail | Bottom navigation |
| Templates | Start from reusable briefs/styles | Left rail | More menu or Library subview |
| Settings | Account, generation, export, and playback preferences | Left rail | Bottom navigation |

### Create workspace

- **Input:** Song brief and musical attributes.
- **Result:** Music preview, generated lyrics, and song structure.
- **Iteration:** Free-text change request plus focused refinement actions.
- **History:** Named versions and variations.
- **Collaboration:** Project collaborators and comments; desktop tab, mobile overflow/project view.

## 5. Responsive layout

### Breakpoints

| Mode | Width | Layout |
| --- | ---: | --- |
| Mobile | 320–767 px | Single column with fixed bottom navigation |
| Tablet | 768–1199 px | Single column or 5/7 split; collapsible navigation |
| Desktop | 1200 px and above | Left rail + top bar + two-column workspace |

Use a centered content maximum of 1680 px. At very wide widths, allow the result region to grow while keeping the composer between 520 and 580 px.

### Desktop frame

- Fixed left navigation rail: **256 px**.
- Top utility bar: **72 px** high, positioned to the right of the rail.
- Workspace padding: **16–20 px**.
- Main grid: composer column **minmax(520px, 560px)** and result column **minmax(680px, 1fr)** with a **16 px** gap.
- Composer is a tall white card. The result side is a stack of cards and compact toolbars.
- Result header contains tabs: **Results**, **Versions (3)**, and **Collaboration**, plus **Save Project** aligned right.

Desktop result grid:

```text
Generated Lyrics (1fr) | Music Preview (1fr)
Song Structure (full width)
Iterate (full width)
Focused actions (full width)
Version History (full width)
```

The left navigation rail includes the MuseForge AI brand at the top and a restrained Mumbai waterfront illustration at the bottom. Treat this illustration as optional ambient branding; it must never compete with controls or reduce text contrast.

### Mobile frame

- One scrollable column, **16 px** side padding, and **12–16 px** vertical gaps.
- Header: brand left; avatar, Save, and overflow actions right.
- No persistent sidebar or desktop utility search.
- Fixed bottom navigation with Create, Library, Projects, and Settings; account for the device safe-area inset.
- Content order:
  1. Song Brief and primary chips
  2. Genre, Tempo, and Vocal Type
  3. Generate Lyrics + Music
  4. Music Preview
  5. Generated Lyrics
  6. Iterate
  7. Song Structure and Version History as collapsed sections below the reference viewport
- Tabs and secondary actions move into section headers, horizontal action rows, or the overflow menu.
- Do not shrink desktop cards side by side. Stack them and preserve comfortable touch targets.

### Responsive behavior mapping

| Desktop element | Mobile behavior |
| --- | --- |
| Left navigation rail | Fixed bottom navigation |
| Search bar | Omitted from Create; available in Library |
| Upgrade, notifications, profile | Profile/overflow menu |
| Results / Versions / Collaboration tabs | Results inline; Versions and Collaboration in overflow or project subviews |
| Lyrics and preview side by side | Preview first, lyrics second |
| Song Structure visible | Collapsible section below iteration |
| Focused iteration action row | Horizontally scrollable action chips below Iterate |
| Version cards in one row | Horizontal snap carousel |
| Save Project button | Save icon in header |

## 6. Visual system

### Color tokens

The palette is deliberately blue-forward and nearly neutral. Avoid large violet surfaces, violet gradients, and purple-tinted shadows.

| Token | Value | Usage |
| --- | --- | --- |
| `--color-brand-600` | `#1769FF` | Primary actions, selected chips, active navigation |
| `--color-brand-500` | `#2F80FF` | Button gradient start, waveform, active progress |
| `--color-brand-100` | `#EAF3FF` | Active navigation background, subtle selected surface |
| `--color-ink-950` | `#07183F` | Headings and high-emphasis text |
| `--color-ink-800` | `#142B57` | Body text and icons |
| `--color-ink-500` | `#61759D` | Supporting text and timestamps |
| `--color-border` | `#D9E4F5` | Cards, inputs, dividers, inactive chips |
| `--color-canvas` | `#F7FAFF` | App background |
| `--color-surface` | `#FFFFFF` | Cards, navigation, inputs |
| `--color-success-soft` | `#ECFAF1` | Chorus structure blocks |
| `--color-warning-soft` | `#FFF5E8` | Bridge structure block |
| `--color-alert` | `#FF3B30` | Notification badge and destructive/error state |

Primary button background may use a subtle left-to-right gradient from `#3A8BFF` to `#1468FF`; both endpoints remain blue.

### Typography

- Font stack: `Inter, SF Pro Display, SF Pro Text, Segoe UI, sans-serif`.
- Display heading: **32/38 px, 700** desktop; **24/30 px, 700** mobile.
- Section title: **17/24 px, 650**.
- Body: **15/22 px, 400** desktop; **16/24 px, 400** in mobile text inputs.
- Label/button: **14/20 px, 600**.
- Supporting/meta: **12/18 px, 400–500**.
- Lyrics: `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`, **14/21 px**.
- Use sentence case. Avoid all caps except metadata supplied by cover art.

### Spacing, radius, elevation

- Spacing scale: **4, 8, 12, 16, 20, 24, 32, 40 px**.
- App/card radius: **14–16 px**.
- Input and button radius: **10–12 px**.
- Chips: **10 px** radius, not fully pill-shaped.
- Card padding: **16 px** compact; **20 px** standard; **24 px** desktop composer.
- Border: **1 px** solid `--color-border`.
- Shadow: `0 8px 28px rgba(26, 71, 140, 0.06)`; use sparingly.

### Iconography and imagery

- Use a consistent rounded outline icon family at 20–24 px.
- Primary blue icons identify creative/output sections; navy icons identify fields and utilities.
- Album artwork is square with a 10–12 px radius.
- Decorative handwritten phrases may appear only as non-essential brand accents. They must be hidden on compact screens and ignored by assistive technology.

## 7. Components

### App brand

Waveform mark + **MuseForge AI** wordmark. “AI” is brand blue; the rest is dark navy. Subtitle: **Ideas to Music. Instantly.**

### Song Brief

- Multiline text area, **500-character maximum**.
- Default reference content: “Create an uplifting Hindi indie-pop song about monsoon evenings in Mumbai.”
- Live counter at bottom right, for example **67/500**.
- **Try an example** inserts a complete, valid brief; it does not generate immediately.
- Preserve line breaks and content when switching views or changing controls.

### Choice chips

Rows wrap naturally; never clip labels.

- Instruments, multi-select: Guitar, Piano, Tabla, Drums, Bass, Strings, Synth.
- Mood, single-select: Happy, Melancholic, Romantic, Energetic, Calm, Epic.
- Language, single-select: Hindi, English, Hinglish, Punjabi, Tamil.
- Selected state: brand-blue fill, white text, blue border.
- Unselected state: white or very pale blue fill, dark text, neutral-blue border.
- Focus state: 2 px brand-blue outer ring with 2 px offset.

### Select fields

Three controls: **Genre**, **Tempo**, and **Vocal Type**.

Reference values:

- Genre: Indie Pop
- Tempo: Medium (100–120 BPM)
- Vocal Type: Male Vocals

Desktop uses a three-column row. Mobile also keeps the three fields in one row at widths around 390 px, with Tempo receiving the most width; below 360 px use a two-column grid and place Vocal Type full width.

### Advanced Options

Desktop: secondary icon button beside Generate.  
Mobile: overflow or expandable row below the primary fields.

May include duration target, song structure planning, seed, model, generation quality, key, time signature, and instrumental/vocal balance. Defaults should be sufficient for first-time generation.

### Primary generation action

- Full-width button: **Generate Lyrics + Music**.
- Leading sparkle icon and trailing arrow.
- Minimum height: **56 px** desktop, **58 px** mobile.
- Disabled until the brief is non-empty and required single-select fields are valid.
- Loading state shows stage text, such as “Writing lyrics…” then “Composing music…”, plus determinate progress when available.
- Completion scrolls/focuses the result without moving the user unexpectedly during generation.

### Music Preview

Contains:

- Title: **Bheegi Mumbai**.
- Metadata: **Indie Pop · Hindi · 3:24**.
- Album artwork and favorite control.
- Waveform with played and unplayed segments.
- Seek position and elapsed/total labels; reference position **0:48 / 3:24**.
- Shuffle, previous, play/pause, next, and repeat controls.
- Overflow menu for export, duplicate, rename, and delete.

The play/pause action is the strongest control: circular, at least **48 × 48 px**, with a pale-blue surface. The waveform must remain keyboard-operable and expose current time, duration, and seek value to assistive technology.

### Generated Lyrics

- Card title and document icon.
- Copy action with success confirmation.
- Scrollable lyrics panel on desktop when needed; expand naturally on mobile up to a reasonable preview height, then offer **Show all**.
- Preserve stanza labels such as `[Verse 1]` and `[Chorus]`.
- Editing is entered through **Refine Lyrics** or an explicit edit mode, not accidental typing in the default result view.

### Song Structure

Horizontal sequence of labeled blocks with start/end time:

- Intro — 0:00–0:15
- Verse 1 — 0:15–0:45
- Chorus — 0:45–1:15
- Verse 2 — 1:15–1:45
- Chorus — 1:45–2:15
- Bridge — 2:15–2:45
- Chorus — 2:45–3:24

Use pale blue for intro/verse, pale green for chorus, and pale orange for bridge. Color supplements the text label; it must not be the only identifier. On mobile, render as a horizontal scroll/snap timeline or a vertically expandable list.

### Iterate

- Prompt: **Tell us how you’d like to change the song.**
- Reference request: “Make it more soulful and add acoustic guitar.”
- Primary action: **Apply Changes**.
- On desktop, input and button share a row. On mobile, stack the button below the input.
- Applying changes creates a new version and never overwrites the active one.

Focused actions:

- Regenerate
- Refine Lyrics
- Change Mood
- Try New Instruments
- Create Variation

Each action preconfigures or opens the smallest necessary editing surface. Regenerate requires confirmation if it would consume a limited credit.

### Version History

Show compact cards with artwork, version number, descriptor, and duration. The reference state contains:

- Version 1 — Uplifting · 3:24
- Version 2 — More soulful · 3:28
- Version 3 — Acoustic vibe · 3:12
- New Variation

The selected version has a 2 px brand-blue outline. Switching versions updates preview, lyrics, structure, and iteration context as one atomic state change.

## 8. Interaction and system states

### Generation states

| State | UI response |
| --- | --- |
| Empty | Composer visible; result region shows concise guidance or a tasteful skeleton illustration |
| Ready | Generate enabled |
| Queued | Button locked; position/status shown if provided by backend |
| Generating | Stage label, progress, Cancel action, and preserved input |
| Partial result | Show completed lyrics/score while audio continues only if supported |
| Complete | Preview receives emphasis; project becomes saveable |
| Failed | Inline error with Retry; preserve brief and every selection |
| Offline | Disable server actions, preserve unsent changes locally, show reconnect status |

### Save behavior

- Changes autosave locally immediately.
- **Save Project** persists the current song, inputs, active version, and history.
- Confirm save with a lightweight status change, not a blocking modal.
- Warn before leaving only when remote persistence has failed.

### Version behavior

- Generate creates Version 1.
- Apply Changes creates the next version.
- Create Variation branches from the active version and records its parent.
- Regenerate creates a new version using the same visible inputs unless the user changes them.
- Restoring an older version changes the active view; it does not delete newer versions.

## 9. Accessibility

- Meet WCAG 2.2 AA color contrast: 4.5:1 for normal text and 3:1 for large text and UI boundaries.
- Minimum interactive target: **44 × 44 px**; prefer **48 × 48 px** for playback.
- Keyboard order follows visual order; no keyboard traps in lyrics, menus, or waveform.
- Every icon-only control has an accessible name and tooltip on pointer devices.
- Selected chips expose `aria-pressed`; single-select groups use radiogroup semantics.
- Announce generation progress and completion through a polite live region; errors use assertive announcement.
- Do not rely on color alone for selected state, song-section type, errors, or waveform progress.
- Respect reduced motion. Animate button and progress changes under 200 ms; avoid ambient motion.
- Bottom navigation and fixed actions must not obscure content at 200% zoom or with large text.

## 10. Content guidelines

- Use direct, creative verbs: Generate, Refine, Change, Try, Create.
- Keep button labels stable between breakpoints.
- Avoid implying that a generation is final; reinforce versioning and reversibility.
- Display language names in their familiar form; generated lyrics may use native script or transliteration based on an Advanced Option.
- Empty-state examples should span languages and moods without stereotyping.

## 11. Suggested component hierarchy

```text
AppShell
├── DesktopSidebar / MobileBottomNav
├── TopBar / MobileHeader
└── CreateWorkspace
    ├── ComposerCard
    │   ├── SongBrief
    │   ├── InstrumentPicker
    │   ├── MoodPicker
    │   ├── LanguagePicker
    │   ├── MusicAttributes
    │   └── GenerateAction
    └── ResultWorkspace
        ├── ResultTabs
        ├── MusicPreview
        ├── LyricsCard
        ├── SongStructure
        ├── IteratePanel
        ├── RefinementActions
        └── VersionHistory
```

On mobile, DOM order should match the mobile reading order: Composer, Music Preview, Lyrics, Iterate, then secondary result sections. CSS reordering must not create a mismatch between visual and keyboard order.

## 12. Minimal data model

```ts
type SongProject = {
  id: string;
  title: string;
  brief: string;
  instruments: string[];
  mood: string;
  language: string;
  genre: string;
  tempo: { label: string; minBpm: number; maxBpm: number };
  vocalType: string;
  activeVersionId: string | null;
  versions: SongVersion[];
  saveState: "local" | "saving" | "saved" | "error";
};

type SongVersion = {
  id: string;
  parentVersionId: string | null;
  number: number;
  label: string;
  durationSeconds: number;
  artworkUrl: string;
  audioUrl: string;
  lyrics: string;
  structure: SongSection[];
  iterationPrompt: string | null;
  createdAt: string;
};
```

## 13. Acceptance criteria

- Desktop at 1440 px shows navigation, composer, lyrics, preview, structure, iterate controls, and version history without horizontal page scrolling.
- Mobile at 390 px uses one content column, keeps the primary Generate and Apply Changes buttons full width, and maintains a safe fixed bottom navigation.
- All reference options and labels are represented consistently across desktop and mobile.
- Selected chips are unmistakable without introducing violet as a dominant hue.
- Music can be played, paused, sought, favorited, and navigated using pointer, touch, and keyboard.
- An iteration produces a new version and preserves the previous one.
- Long lyrics, long briefs, localization, loading, errors, offline mode, and empty states do not break the layout.
- The mobile view preserves access to Song Structure, focused refinement actions, Version History, Collaboration, Templates, and Advanced Options through progressive disclosure.

## 14. Scope note

This specification defines the responsive product UI shown in the two reference mockups. The visuals suggest generated stereo music and versioned creative iteration; they do not imply editable DAW stems or native multi-track notation. Those capabilities require separate product and data-model extensions.
