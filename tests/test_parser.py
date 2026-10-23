"""Acceptance tests for parse_bank_csv: raw upload bytes in, valid rows and row errors out.

The parser never fails the whole upload for one bad row: valid rows come back as
TransactionRow, bad rows as {"row", "reason"} entries (D-009 to D-011).
"""

from decimal import Decimal
from pathlib import Path

from finance_api.ingest.parser import parse_bank_csv

FIXTURES = Path(__file__).parent / "fixtures"
UTF8_BOM = b"\xef\xbb\xbf"
ACCENTED_CSV = "Fecha;Concepto;Importe\n09/10/2026;COMPRA CAFETERÍA PEÑA;-4,20\n"


def read_fixture(name: str) -> bytes:
    """Return a fixture's raw bytes, exactly as an upload would deliver them."""
    return (FIXTURES / name).read_bytes()


def test_valid_rows_are_returned_in_file_order() -> None:
    """All 7 valid rows come back, including both identical coffees (dedupe is the DB's job)."""
    rows, _ = parse_bank_csv(read_fixture("bank_sample.csv"))

    assert len(rows) == 7
    assert rows[0].description == "COMPRA MERCADONA BARCELONA"
    assert [row.description for row in rows].count("CAFE SOL BARCELONA") == 2


def test_bad_row_is_reported_with_file_line_and_clean_reason() -> None:
    """31/02 sits on line 7 of the file (header = 1, D-010), without Pydantic's prefix (D-011)."""
    _, errors = parse_bank_csv(read_fixture("bank_sample.csv"))

    assert errors == [{"row": 7, "reason": "invalid date '31/02/2026'"}]


def test_saldo_export_parses_balance() -> None:
    """Exports with a Saldo column go through the same parser (D-006)."""
    rows, errors = parse_bank_csv(read_fixture("bank_sample_saldo.csv"))

    assert len(rows) == 7
    assert rows[0].balance == Decimal("1457.65")
    assert errors == [{"row": 7, "reason": "invalid date '31/02/2026'"}]


def test_utf8_bom_does_not_hide_first_header() -> None:
    """With a BOM read as plain UTF-8 the header is '\\ufeffFecha' and every row fails (D-009)."""
    rows, errors = parse_bank_csv(UTF8_BOM + read_fixture("bank_sample.csv"))

    assert len(rows) == 7
    assert len(errors) == 1


def test_cp1252_export_keeps_accents() -> None:
    """A Windows export decodes through the cp1252 fallback with Í, Ñ, Ó, É intact (D-009)."""
    rows, errors = parse_bank_csv(read_fixture("bank_sample_cp1252.csv"))

    assert [row.description for row in rows] == ["COMPRA CAFETERÍA PEÑA", "ÓPTICA SAN JOSÉ"]
    assert errors == []


def test_utf8_accents_are_not_read_as_cp1252() -> None:
    """UTF-8 must be tried first: cp1252 would turn 'Ñ' into 'Ã‘' without raising."""
    rows, _ = parse_bank_csv(ACCENTED_CSV.encode("utf-8"))

    assert rows[0].description == "COMPRA CAFETERÍA PEÑA"


def test_missing_column_falls_back_to_pydantic_message() -> None:
    """Pydantic's own errors have no ctx, so the reason falls back to its msg (D-011)."""
    _, errors = parse_bank_csv(b"Fecha;Importe\n03/10/2026;-1,00\n")

    assert errors == [{"row": 2, "reason": "Field required"}]


def test_row_with_two_problems_reports_both_in_one_entry() -> None:
    """One entry per rejected row, so len(errors) is the rejected count; no reason is hidden."""
    _, errors = parse_bank_csv(b"Fecha;Concepto;Importe\n31/02/2026;CAFE SOL;abc\n")

    assert errors == [{"row": 2, "reason": "invalid date '31/02/2026'; invalid amount 'abc'"}]


def test_header_only_file_returns_nothing() -> None:
    """A file with no transactions is not an error, just an empty result."""
    assert parse_bank_csv(b"Fecha;Concepto;Importe\n") == ([], [])
