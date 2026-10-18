# Engineering decisions

One entry per decision. Each lists the options I considered, what I chose, the limitations I accepted, and what would make me revisit it.

## D-001: Repository conventions (2026-10-18, portfolio setup)
**Context:** Setting up six portfolio repos (IHB-01 to IHB-06) at once, before any feature work.
**Options considered:**
| Decision | Option | Pros | Cons / limitations |
| --- | --- | --- | --- |
| Scope | All 6 repos now | Portfolio reads as one series from day one | Later projects sit near-empty for months |
| Scope | Flagships only, rest later | No empty repos | Setup repeated 4 more times |
| Visibility | Public | Visible commit history; unlimited free GitHub Actions minutes | Unfinished work is visible |
| Visibility | Private, flip later | Polish before showing | Hides progress; Actions capped at 2,000 free min/month |
| Naming | `ihb-0X-name` | Sorts as a series; signature in the URL | Renumbering means a rename (GitHub redirects) |
| Naming | `name` only | Shorter | Weaker series signature |
| Contents | Starter skeleton | README, license, docs ready to fill | Kit banners added later |
| Contents | Empty repo | First commit is the real kickoff | Visitors see GitHub's setup page |
**Decision:** All 6 repos now, public, `ihb-0X-name`, starter skeleton. Chosen by me.
**Why:** A portfolio built in public shows steady progress, and the free Actions minutes fit a zero-budget setup.
**Limitations accepted:** Repos for later projects look unstarted until their kickoff; the status badge says "in progress" to set expectations.
**Revisit if:** A project needs private or employer data (make that repo private), or a project is dropped (archive it instead of leaving it empty).
