"""Turn the raw bytes of a bank CSV upload into validated rows and per-row errors.

upload bytes
    │ decode: utf-8-sig, else cp1252                         (D-009)
    ▼
csv.DictReader(";") ──▶ one dict per line, numbered from 2   (D-010)
    │
    ▼
TransactionRow.model_validate(row)
    ├──▶ ✓ rows:   [TransactionRow, ...]
    └──▶ ✗ errors: [{"row": 7, "reason": "invalid date '31/02/2026'"}]
                    reason = ctx["error"], else msg          (D-011)
"""

import csv
import io
from typing import TypedDict

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from finance_api.ingest.schemas import TransactionRow

# The header is line 1, so the first transaction is line 2: the number an editor shows (D-010).
FIRST_DATA_LINE = 2


class RowError(TypedDict):
    """One rejected row in the upload report."""

    row: int  # line in the file, header = 1 (D-010)
    reason: str  # our validator's message, or Pydantic's for built-in errors (D-011)


def decode_bank_bytes(raw: bytes) -> str:
    """Decode an export as UTF-8 (with or without BOM), falling back to cp1252 (D-009).

    UTF-8 goes first because it is strict: cp1252 bytes for accented letters are invalid
    UTF-8, so a cp1252 file always fails here and never gets misread. The reverse order
    would not work, because cp1252 accepts almost any byte and would garble UTF-8 silently.
    """
    try:
        # utf-8-sig drops a leading BOM; plain utf-8 would glue it to the first header
        # ('﻿Fecha') and every row would fail with "Field required".
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Only this error falls back: anything else is a bug, not an encoding question.
        return raw.decode("cp1252")


def error_reason(error: ErrorDetails) -> str:
    """Return the message our validator raised, or Pydantic's own message (D-011).

    "ctx" only exists for errors raised inside our validators; Pydantic's built-in errors
    such as "Field required" have no ctx and no prefix, so their msg is already clean.
    """
    ctx = error.get("ctx")
    if ctx and "error" in ctx:
        return str(ctx["error"])
    return error["msg"]


def parse_bank_csv(raw: bytes) -> tuple[list[TransactionRow], list[RowError]]:
    """Decode, read and validate every row of a bank CSV export.

    Args:
        raw: The uploaded file, byte for byte.

    Returns:
        Valid rows in file order, and one error entry per rejected row. Duplicates are
        kept: deciding what is a re-upload is the database's job (D-006).
    """
    text = decode_bank_bytes(raw)
    # newline="" hands line endings to the csv module, which needs them to keep a line break
    # inside a quoted description as part of the cell (Python docs, csv.reader).
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";")

    rows: list[TransactionRow] = []
    errors: list[RowError] = []
    # enumerate, not reader.line_num: line_num reports where a record ends, so a multi-line
    # quoted cell would shift the number past the row's first line (D-010).
    for line_number, raw_row in enumerate(reader, start=FIRST_DATA_LINE):
        try:
            rows.append(TransactionRow.model_validate(raw_row))
        except ValidationError as exc:
            # One entry per row with every reason joined, so len(errors) is the rejected
            # count and a second problem in the same row is not hidden.
            reason = "; ".join(error_reason(error) for error in exc.errors())
            errors.append({"row": line_number, "reason": reason})
    return rows, errors
