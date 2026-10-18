"""Acceptance tests for TransactionRow: one bank CSV row, validated.

Rows are passed as the dicts csv.DictReader yields, keyed by the bank's Spanish headers,
so the model must map Fecha/Concepto/Importe to date/description/amount itself.
"""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from finance_api.ingest.schemas import TransactionRow


def make_row(
    fecha: str = "03/10/2026", concepto: str = "COMPRA MERCADONA BARCELONA", importe: str = "-42,35"
) -> dict[str, str]:
    """Build a raw CSV row with valid defaults, so each test changes only one field."""
    return {"Fecha": fecha, "Concepto": concepto, "Importe": importe}


def test_valid_row_is_parsed_to_python_types() -> None:
    """Spanish date and decimal comma become date and Decimal."""
    row = TransactionRow.model_validate(make_row())

    assert row.date == date(2026, 10, 3)
    assert row.description == "COMPRA MERCADONA BARCELONA"
    assert row.amount == Decimal("-42.35")


def test_thousands_separator_is_removed() -> None:
    """'2.100,00' is two thousand one hundred, not two point one."""
    row = TransactionRow.model_validate(make_row(importe="2.100,00"))

    assert row.amount == Decimal("2100.00")


def test_amount_is_exact_decimal_not_float() -> None:
    """Amounts must be Decimal so sums never drift (0.1 + 0.2 != 0.3 in float)."""
    row = TransactionRow.model_validate(make_row(importe="-0,10"))

    assert isinstance(row.amount, Decimal)
    assert row.amount == Decimal("-0.10")


def test_description_is_stripped() -> None:
    """Exports often pad text fields; padding must not create 'different' merchants."""
    row = TransactionRow.model_validate(make_row(concepto="  CAFE SOL  "))

    assert row.description == "CAFE SOL"


def test_impossible_date_is_rejected_with_reason() -> None:
    """31 February matches dd/mm/yyyy but does not exist; the error names the bad value."""
    with pytest.raises(ValidationError) as exc_info:
        TransactionRow.model_validate(make_row(fecha="31/02/2026"))

    assert "invalid date '31/02/2026'" in str(exc_info.value)


def test_iso_date_is_rejected() -> None:
    """Only the bank's dd/mm/yyyy is accepted, so a swapped format can't slip in silently."""
    with pytest.raises(ValidationError):
        TransactionRow.model_validate(make_row(fecha="2026-10-03"))


def test_non_numeric_amount_is_rejected_with_reason() -> None:
    """A garbled amount is reported, not turned into 0."""
    with pytest.raises(ValidationError) as exc_info:
        TransactionRow.model_validate(make_row(importe="abc"))

    assert "invalid amount 'abc'" in str(exc_info.value)


def test_empty_description_is_rejected() -> None:
    """A row without a description can't be categorized or deduplicated."""
    with pytest.raises(ValidationError):
        TransactionRow.model_validate(make_row(concepto="   "))


def test_row_without_saldo_has_no_balance() -> None:
    """Exports without a Saldo column are valid; balance is simply unknown."""
    row = TransactionRow.model_validate(make_row())

    assert row.balance is None


def test_saldo_is_parsed_like_amount() -> None:
    """Saldo uses the same Spanish format as Importe, including thousands separators."""
    raw = make_row() | {"Saldo": "1.457,65"}

    row = TransactionRow.model_validate(raw)

    assert row.balance == Decimal("1457.65")


def test_invalid_saldo_is_rejected_with_reason() -> None:
    """A garbled balance is reported under its own field name, not as an amount error."""
    raw = make_row() | {"Saldo": "n/a"}

    with pytest.raises(ValidationError) as exc_info:
        TransactionRow.model_validate(raw)

    assert "invalid balance 'n/a'" in str(exc_info.value)


def test_blank_saldo_means_unknown_balance() -> None:
    """A blank Saldo cell (';;') is a missing balance, not a broken row."""
    raw = make_row() | {"Saldo": "  "}

    row = TransactionRow.model_validate(raw)

    assert row.balance is None
