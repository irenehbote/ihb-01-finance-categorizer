# Style guide · IHB-01 Finance Categorizer

Lab Notebook visual system, shared by all IHB repos, with this project's accent: **ledger green**.
Every diagram, chart, UI and README visual uses only the tokens below. A new token is proposed
and logged in [DECISIONS.md](DECISIONS.md) before it's used.

> **Status:** started early (D-008) so learning diagrams are consistent from day one. Banners,
> results cards, `portfolio.mplstyle`, the README template and the icon set come from the
> Lab Notebook kit and are added once the kit is in the repo.

## Design tokens

```css
/* Lab Notebook tokens + IHB-01 accent. CSS variables work in plain HTML, Gradio custom CSS
   and React alike, so one file serves every surface of the project. */
:root {
  --font-heading: "Fraunces", Georgia, serif;          /* titles and section headings only */
  --font-body: "DM Sans", system-ui, sans-serif;       /* body and UI */
  --font-mono: "JetBrains Mono", ui-monospace, monospace; /* data, code, IDs, metrics */

  --text-xs: 12px; --text-sm: 14px; --text-md: 16px; --text-lg: 20px; --text-xl: 28px;
  --space-1: 4px; --space-2: 8px; --space-3: 16px; --space-4: 24px; --space-5: 32px;

  --color-bg: #FBFAF6;        /* paper */
  --color-text: #1B2A2F;      /* ink */
  --color-muted: #5F6B6E;
  --color-grid: #E6E3D9;
  --color-signature: #24466B; /* notebook ink blue, all IHB repos */
  --color-accent: #1F7A5A;    /* ledger green, IHB-01 */

  --radius: 6px;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #121614;
    --color-text: #E8E6DF;
    --color-muted: #9AA39F;
    --color-grid: #2A302D;
    --color-signature: #8FB3D9;
    /* Overridden on purpose: the light accent is only 3.47:1 on the dark background (D-008). */
    --color-accent: #5CC29A;
  }
}
```

## Contrast check (WCAG, text needs ≥ 4.5:1)

| Mode | Text | Background | Ratio | Result |
| --- | --- | --- | --- | --- |
| Light | ink `#1B2A2F` | paper `#FBFAF6` | 14.17:1 | ✓ |
| Light | muted `#5F6B6E` | paper `#FBFAF6` | 5.27:1 | ✓ |
| Light | signature `#24466B` | paper `#FBFAF6` | 9.29:1 | ✓ |
| Light | accent `#1F7A5A` | paper `#FBFAF6` | 5.04:1 | ✓ |
| Light | ink `#1B2A2F` | grid `#E6E3D9` | 11.53:1 | ✓ |
| Light | muted `#5F6B6E` | grid `#E6E3D9` | 4.29:1 | ✗ never use |
| Dark | text `#E8E6DF` | bg `#121614` | 14.61:1 | ✓ |
| Dark | muted `#9AA39F` | bg `#121614` | 7.05:1 | ✓ |
| Dark | signature `#8FB3D9` | bg `#121614` | 8.36:1 | ✓ |
| Dark | accent `#5CC29A` | bg `#121614` | 8.38:1 | ✓ |
| Dark | light accent `#1F7A5A` | bg `#121614` | 3.47:1 | ✗ never use |
| Dark | text `#E8E6DF` | grid `#2A302D` | 10.79:1 | ✓ |

**Rules that follow:** text on a grid-colored fill is always ink, never muted. Dark mode always
uses the dark accent.

## Type and spacing

- 5 sizes only: 12 / 14 / 16 / 20 / 28 px. 2 weights: regular 400 and semibold 600 (headings).
- Every margin and padding is a multiple of 4 px; cards use 16 or 24 px padding.
- 6 px radius, 1 px hairline borders in the grid color, no heavy shadows.

## Diagrams

Diagrams are the main way I learn this codebase, so every session adds at least one.

| Where | Format | Why |
| --- | --- | --- |
| `docs/LEARNING_LOG.md`, README | Mermaid in Markdown | Text-based, diffs like code, renders on GitHub |
| Module docstrings | ASCII sketch, ≤ 12 lines | Editors don't render Mermaid; the sketch lives next to the code it explains |
| Chat explanations | Inline SVG, same roles and hex values | Shown while learning, not stored |

### Node roles

Meaning comes from **shape, border and a ✓ / ✗ / (planned) label**, never from color alone.

| Role | Look | Use for |
| --- | --- | --- |
| `step` | paper fill, ink-blue border | What the code does |
| `good` | paper fill, 2 px ledger-green border, label starts with ✓ | Correct outcomes |
| `bad` | grid fill, dashed muted border, label starts with ✗ | Bugs and wrong paths the code avoids |
| `planned` | paper fill, dashed muted border, muted text, "(planned)" | Features not built yet |

Shapes: `[( )]` database, `[/ /]` file or input, `{ }` decision, `[ ]` everything else.

### Mermaid snippet (paste at the end of every diagram)

```text
classDef step fill:#FBFAF6,stroke:#24466B,color:#1B2A2F
classDef good fill:#FBFAF6,stroke:#1F7A5A,stroke-width:2px,color:#1B2A2F
classDef bad fill:#E6E3D9,stroke:#5F6B6E,stroke-dasharray:4 3,color:#1B2A2F
classDef planned fill:#FBFAF6,stroke:#5F6B6E,stroke-dasharray:4 3,color:#5F6B6E
```

Fills are fixed paper tones, so nodes stay readable on GitHub's dark theme too (ink on paper
is 14.17:1). Limitation: Mermaid on GitHub can't load Fraunces or DM Sans, so diagrams use
GitHub's font.

### Diagram rules

- One concept per diagram, at most ~9 nodes; split bigger flows.
- `flowchart LR` for pipelines, `flowchart TD` for hierarchies and before/after comparisons.
- Real values in labels (`'2.100,00'`, `hash A`), not placeholders.
- A one-line caption above the diagram states what it shows.
