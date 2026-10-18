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

## D-002: Dependency manager (2026-10-18, project setup)
**Context:** Need a reproducible Python environment for a FastAPI service whose ML-vs-LLM benchmark must be re-runnable later on another machine or in CI.
**Options considered:**
| Option | Pros | Cons / limitations |
| --- | --- | --- |
| pip + venv | Built into Python; universal `requirements.txt` | No lockfile of transitive deps; slow; manual venv handling |
| uv | Very fast; `uv.lock` pins every transitive dep; manages Python versions; exports `requirements.txt` | Young tool (2024), single-company ownership |
| poetry | Mature lockfile, good for publishing libraries | Slower resolver; built for libraries, not apps; losing mindshare to uv |
**Decision:** uv, chosen by me.
**Why:** Exact, lockfile-based environments make the accuracy/cost comparison reproducible; `uv export` still gives a pinned `requirements.txt` for deploys.
**Limitations accepted:** One more tool to install; on this machine uv needs `--system-certs` because local HTTPS inspection uses a certificate only the Windows store trusts.
**Revisit if:** A deploy target or team standard requires plain pip/poetry.

## D-003: Package layout (2026-10-18, project setup)
**Context:** The app will be containerized and deployed, so import and packaging bugs should surface locally, not in Docker.
**Options considered:**
| Option | Pros | Cons / limitations |
| --- | --- | --- |
| `src/` layout | Tests import the installed package, catching packaging bugs early; PyPA-recommended; uv default | Needs `pyproject.toml` + editable install |
| Flat layout | Zero setup | Imports from the working folder hide packaging bugs until deploy |
**Decision:** `src/` layout (`src/finance_api/`), chosen by me.
**Why:** A deployed service benefits from tests that run against the installed package.
**Limitations accepted:** Slightly more setup; `python script.py` from the repo root won't find the package without the venv.
**Revisit if:** Never for this project; flat is only better for script/notebook-only repos.

## D-004: Keep all personal data out of git (2026-10-18, project setup)
**Context:** The repo is public and processes my real bank statements.
**Options considered:** Only one reasonable option. Ignoring just `data/raw/` would still leak hand labels and the SQLite DB built from real transactions.
**Decision:** Gitignore everything in `data/` except `data/README.md`, plus `*.db`, `*.sqlite`, `*.sqlite3`. Tests use synthetic CSVs in `tests/fixtures/`.
**Why:** A leaked statement can't be un-published (forks and caches keep it).
**Limitations accepted:** Evaluation data can't be shared; the README will describe the dataset instead.
**Revisit if:** I build a fully synthetic labeled dataset that is safe to publish.
