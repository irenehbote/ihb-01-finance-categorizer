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

## D-005: Database access layer (2026-10-18, Feature 1.1)

**Context:** Store uploaded transactions in SQLite, with a uniqueness rule for duplicates.

**Options considered:**

| Option | Pros | Cons / limitations |
| --- | --- | --- |
| SQLAlchemy 2.0 | Typed models; constraints declared in code; Postgres is a URL change; common in job postings | Learning curve; generated SQL is hidden |
| raw sqlite3 | Stdlib, explicit SQL, `INSERT OR IGNORE` | Manual row mapping; SQL in strings; tied to SQLite |

**Decision:** SQLAlchemy 2.0, chosen by me.

**Why:** Portable and typed; IHB-04 (SQL agent) already covers hand-written SQL.

**Limitations accepted:** More abstraction; I'll check the emitted SQL with `echo=True` when debugging.

**Revisit if:** The schema stays one table and the ORM adds more friction than value.

## D-006: Duplicate detection (2026-10-18, Feature 1.1)

**Context:** Uploading the same CSV twice must not double my data, but two identical real purchases (same café, same day, same amount) must both be kept. My export has no Saldo (balance) column, but the code must also handle exports that do.

**Options considered:**

| Option | Pros | Cons / limitations |
| --- | --- | --- |
| Composite UNIQUE constraint | DB enforces it | Whitespace/case variants slip through; long key |
| Row hash checked in code | Normalization in one place | Check-then-insert race; no DB guarantee |
| Hash column + UNIQUE | Normalization and DB guarantee | Changing normalization means re-hashing old rows |

**Follow-up: how to use Saldo when present:**

| Option | Pros | Cons / limitations |
| --- | --- | --- |
| A. Saldo replaces occurrence count | Best key per format | Two code paths to test |
| B. Ignore Saldo for dedupe | One path; works across mixed formats | Wastes the best uniqueness signal |
| C. Occurrence count + Saldo when present | One path; Saldo removes the mid-day-cut edge case | Same account exported with and without Saldo won't dedupe across formats |

**Decision:** Hash + UNIQUE, chosen by me. Hash input: normalized date, description, amount, the row's occurrence count among identical rows in the same file, plus Saldo when the export has it (option C).

**Why:** Re-uploads produce identical hashes and are skipped; identical legitimate rows get occurrence 1, 2 and are both kept.

**Limitations accepted:** Without Saldo, an export that cuts a day in half can miss one identical row. Mixing exports with and without Saldo for the same account creates duplicates.

**Revisit if:** I start mixing export formats for one account (switch to option B).

## D-007: CSV parsing (2026-10-18, Feature 1.1)

**Context:** Bad rows must be reported with their row number without failing the whole upload.

**Options considered:**

| Option | Pros | Cons / limitations |
| --- | --- | --- |
| csv module | Row by row, exact row numbers, each row straight into Pydantic, no dependency | More code; encoding handled manually |
| pandas | One-line `read_csv` | Column-wise parsing hides per-row errors (`NaT`); amounts default to float; ~50 MB dependency |

**Decision:** csv module (`DictReader`, `;` delimiter), chosen by me.

**Why:** Per-row validation and error reporting is the core requirement, and Pydantic is already the validator.

**Limitations accepted:** Encoding (UTF-8 vs cp1252) must be detected or configured by me.

**Revisit if:** I need bulk transformations over many files.

## D-008: Visual learning system and early STYLE.md (2026-10-18, project-wide)

**Context:** I learn best visually, so every concept should come with a diagram in my Lab Notebook style. Rule: visuals follow `docs/STYLE.md`, which didn't exist yet, and the Lab Notebook kit isn't in the repo.

**Options considered:** Only one reasonable format for in-repo diagrams: Mermaid. It's text (diffs and reviews like code) and GitHub renders it. Exported SVG/PNG can't be diffed, and the kit's SVG generator isn't available yet.

**Decision:** Start `docs/STYLE.md` now with the tokens, a contrast check and diagram conventions (4 node roles: step, good ✓, bad ✗, planned). Diagrams go in three places: Mermaid in the learning log and README, ASCII sketches in module docstrings, inline SVG in chat. New token use: the dark-mode accent override `#5CC29A`.

**Why:** The contrast check showed the light accent `#1F7A5A` is 3.47:1 on the dark background and muted text on the grid fill is 4.29:1, both below 4.5:1, so those pairs are banned in STYLE.md.

**Limitations accepted:** Mermaid on GitHub can't load Fraunces or DM Sans, so it uses GitHub's font. Learning diagrams don't count toward the 5-session visual polish budget, which stays for UI, charts and README polish.

**Revisit if:** The kit arrives (add banners, results card, mplstyle) or a diagram needs exact layout Mermaid can't do (switch that one to SVG).

## D-009: File encoding (2026-10-23, Feature 1.1)

**Context:** Spanish bank exports come as UTF-8 (sometimes with a BOM) or as Windows cp1252. Decoding with the wrong one turns `CAFETERÍA` into `CAFETERÃ…`, and a BOM read as plain UTF-8 makes the first header `'﻿Fecha'`, so the `Fecha` alias never matches and every row is rejected.

**Options considered:**

| Option | Pros | Cons / limitations |
| --- | --- | --- |
| A. `utf-8-sig` only, reject otherwise | Simple; never stores garbled text | A cp1252 export is rejected whole |
| B. `utf-8-sig`, fall back to `cp1252` | Covers both common Spanish bank formats | A third encoding is misread by cp1252 without an error |
| C. `charset-normalizer` detection | Handles many encodings | New dependency; guesses can be wrong on small files |

**Decision:** B, chosen by me.

**Why:** Strict UTF-8 is a reliable detector: cp1252 bytes for `Í` or `Ñ` are invalid UTF-8 (checked), so trying UTF-8 first never accepts a cp1252 file by mistake. `utf-8-sig` strips the BOM when present and is identical to `utf-8` when not.

**Limitations accepted:** A file in a third encoding (e.g. Latin-9 with `€`, or UTF-16) is decoded as cp1252 and can be silently wrong.

**Revisit if:** A real export shows garbled descriptions after upload, or I add a bank that exports UTF-16.

## D-010: Row number in upload errors (2026-10-23, Feature 1.1)

**Context:** Each rejected row is reported as `{"row", "reason"}`. "Row" can mean the line in the file or the position among transactions.

**Options considered:**

| Option | Pros | Cons / limitations |
| --- | --- | --- |
| A. File line (header = 1, first transaction = 2) | Matches what an editor or Excel shows | Needs a note that row 2 is the first transaction |
| B. Transaction index (first = 1) | Intuitive without opening the file | Matches no editor |

**Decision:** A, chosen by me. Counted with `enumerate(reader, start=2)`.

**Why:** The number exists so I can open the file and find the bad row; it should point at the same line the editor shows. In the fixtures, `31/02/2026` is line 7.

**Limitations accepted:** A quoted description containing a line break spans two file lines; the count then numbers records, not physical lines. `reader.line_num` was rejected because it reports where a record ends, not where it starts.

**Revisit if:** A real export contains multi-line quoted fields.

## D-011: Reason text in upload errors (2026-10-23, Feature 1.1)

**Context:** Pydantic prefixes errors raised by our validators with `"Value error, "`, e.g. `"Value error, invalid date '31/02/2026'"`. The report should show only our message.

**Options considered:**

| Option | Pros | Cons / limitations |
| --- | --- | --- |
| A. `msg.removeprefix("Value error, ")` | One line | Tied to Pydantic's wording, which can change on upgrade |
| B. `err["ctx"]["error"]`, falling back to `msg` | Returns our own `ValueError` text unchanged | Pydantic's built-in errors ("Field required") have no `ctx`, so the fallback is required |
| C. Keep `msg` as is | No code | Users see the `"Value error, "` noise |

**Decision:** B, chosen by me.

**Why:** `ctx["error"]` is the exception our validator raised, so the text is exactly what `schemas.py` wrote (checked). Built-in errors keep Pydantic's message, which has no prefix to strip.

**Limitations accepted:** Built-in messages don't name the column; `err["loc"]` (the Spanish alias, e.g. `('Fecha',)`) can be added if that turns out to be confusing.

**Revisit if:** A Pydantic upgrade changes the shape of `ctx`, or errors without a column name confuse me in real uploads.
