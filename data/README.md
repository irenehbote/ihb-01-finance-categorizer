# data/

Everything in this folder except this file is gitignored, because it holds my real banking data and this repo is public.

- `raw/`: bank CSV exports, as downloaded.
- `labeled/`: hand-labeled transactions used as ground truth for evaluation.

Tests never read from here; they use synthetic CSVs in `tests/fixtures/`.
