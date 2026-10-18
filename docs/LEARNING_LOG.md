# Learning log

One entry per session: steps taken, concepts learned, problems hit and how I solved them.

## Session 0 (2026-10-18) - Portfolio setup
**Steps taken:**
1. Created the six IHB repos on GitHub (public) through the REST API.
2. Added a starter skeleton to each: README stub with a results row, MIT license, Python .gitignore, decision and learning logs.
**Concepts learned:** Architecture Decision Records (ADRs) as an industry practice; why public repos get unlimited free GitHub Actions minutes.
**Problems + fixes:** No `gh` CLI on Windows -> used the Git Credential Manager token with `curl --ssl-no-revoke` to call the GitHub API.
**Decisions made:** D-001.
**Next session starts with:** Kickoff of the first feature, plus locating the Lab Notebook kit for banners and README_TEMPLATE.md.

## Session 1 (2026-10-18) - Project setup, session 1 of 1
**Steps taken:**
1. Hardened `.gitignore` so all of `data/` and any SQLite file stay out of the public repo.
2. Installed uv and initialized a `src/` package (`finance_api`) with folders for api, ingest, db, categorize and evaluation.
3. Added runtime deps (fastapi, uvicorn, python-multipart) and dev deps (pytest, httpx2, ruff); exported a pinned `requirements.txt`.
4. Added a `/health` endpoint and a smoke test (passing); ruff lint + format clean.
**Concepts learned:** Lockfile vs `requirements.txt` (direct vs transitive pins); why `src/` layout makes tests run against the installed package; liveness checks shouldn't depend on downstream services.
**Problems + fixes:** uv failed with `invalid peer certificate: UnknownIssuer` -> `--system-certs` makes uv use the Windows certificate store. Starlette 1.8 warned that `httpx` is deprecated for TestClient -> replaced with `httpx2`.
**Decisions made:** D-002, D-003, D-004.
**Next session starts with:** Feature 1.1 (CSV upload), with decisions on ORM vs raw SQL, duplicate detection, and pandas vs csv module. Bring one real bank export to check encoding, thousands separator and whether there's a Saldo column.
