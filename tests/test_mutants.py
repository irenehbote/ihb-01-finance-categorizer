"""Mutation tests: prove each row-model test can actually fail.

A test that still passes against broken code gives false confidence. Each mutant below is
the real schemas.py with one deliberate bug, and the test it targets must fail against it.

    schemas.py ──patch one line──▶ mutant ──run target test──┬──▶ fails   ✓ caught
                                                             └──▶ passes  ✗ test too weak

Mutants are built by patching the live source at test time instead of storing 12 edited
copies: copies would drift from schemas.py, while a patch whose target line no longer
exists fails loudly and forces the mutant to be updated.
"""

import types
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import pytest
import test_row_model as row_tests

import finance_api.ingest.schemas as schemas

SCHEMAS_SOURCE = Path(schemas.__file__).read_text(encoding="utf-8")


class Mutant(NamedTuple):
    """One deliberate bug and the test that must catch it."""

    test: Callable[[], None]
    bug: str
    old: str
    new: str


MUTANTS = [
    Mutant(
        row_tests.test_valid_row_is_parsed_to_python_types,
        "reads dates as mm/dd/yyyy (03/10 becomes 10 March)",
        'BANK_DATE_FORMAT = "%d/%m/%Y"',
        'BANK_DATE_FORMAT = "%m/%d/%Y"',
    ),
    Mutant(
        row_tests.test_thousands_separator_is_removed,
        "converts the decimal comma before removing thousands dots",
        '.replace(".", "").replace(",", ".")',
        '.replace(",", ".").replace(".", "")',
    ),
    Mutant(
        row_tests.test_amount_is_exact_decimal_not_float,
        "stores amounts as float",
        'amount: Decimal = Field(alias="Importe")',
        'amount: float = Field(alias="Importe")',
    ),
    Mutant(
        row_tests.test_description_is_stripped,
        "keeps padding around descriptions",
        "return value.strip()",
        "return value",
    ),
    Mutant(
        row_tests.test_impossible_date_is_rejected_with_reason,
        "rejects bad dates with a vague message",
        """raise ValueError(f"invalid date '{value}'") from exc""",
        'raise ValueError("bad date") from exc',
    ),
    Mutant(
        row_tests.test_iso_date_is_rejected,
        "silently accepts ISO dates as a fallback",
        "return dt.datetime.strptime(value.strip(), BANK_DATE_FORMAT).date()",
        "return dt.date.fromisoformat(value.strip()) if '-' in value"
        " else dt.datetime.strptime(value.strip(), BANK_DATE_FORMAT).date()",
    ),
    Mutant(
        row_tests.test_non_numeric_amount_is_rejected_with_reason,
        "lets InvalidOperation escape instead of re-raising ValueError",
        "except InvalidOperation as exc:",
        "except ZeroDivisionError as exc:",
    ),
    Mutant(
        row_tests.test_empty_description_is_rejected,
        "accepts whitespace-only descriptions",
        "if not isinstance(value, str) or not value.strip():",
        "if not isinstance(value, str):",
    ),
    Mutant(
        row_tests.test_row_without_saldo_has_no_balance,
        "defaults a missing balance to 0 instead of unknown",
        'balance: Decimal | None = Field(default=None, alias="Saldo")',
        'balance: Decimal | None = Field(default=Decimal("0"), alias="Saldo")',
    ),
    Mutant(
        row_tests.test_saldo_is_parsed_like_amount,
        "maps balance to the wrong CSV header",
        'Field(default=None, alias="Saldo")',
        'Field(default=None, alias="Balance")',
    ),
    Mutant(
        row_tests.test_invalid_saldo_is_rejected_with_reason,
        "reports balance errors as amount errors",
        'parse_spanish_decimal(value, "balance")',
        'parse_spanish_decimal(value, "amount")',
    ),
    Mutant(
        row_tests.test_blank_saldo_means_unknown_balance,
        "rejects blank Saldo cells instead of treating them as unknown",
        "if value is None or (isinstance(value, str) and not value.strip()):",
        "if value is None:",
    ),
]


def build_mutant(old: str, new: str) -> type:
    """Return TransactionRow compiled from schemas.py with one text patch applied.

    Raises:
        AssertionError: If the patch target isn't found exactly once. Failing here, not
            skipping, is deliberate: a stale mutant would otherwise test nothing.
    """
    assert SCHEMAS_SOURCE.count(old) == 1, f"patch target not found exactly once: {old!r}"
    module = types.ModuleType("schemas_mutant")
    exec(compile(SCHEMAS_SOURCE.replace(old, new), "<mutant>", "exec"), module.__dict__)
    return module.TransactionRow


@pytest.mark.parametrize("mutant", MUTANTS, ids=lambda m: m.test.__name__)
def test_mutant_is_caught(mutant: Mutant, monkeypatch: pytest.MonkeyPatch) -> None:
    """The target test must fail when TransactionRow has the mutant's bug."""
    # Built outside the try block: a mutant that doesn't compile is a broken mutant,
    # and must not be miscounted as "caught".
    mutant_row = build_mutant(mutant.old, mutant.new)
    monkeypatch.setattr(row_tests, "TransactionRow", mutant_row)

    try:
        mutant.test()
    except (Exception, pytest.fail.Exception):
        # Any failure counts: an assertion, a missing ValidationError ("DID NOT RAISE"),
        # or an exception escaping the model all mean the test noticed the bug.
        return
    pytest.fail(f"{mutant.test.__name__} did not detect the bug: {mutant.bug}")


def test_every_row_test_has_a_mutant() -> None:
    """Adding a row test without a mutant fails here, so coverage can't silently shrink."""
    row_test_names = {name for name in dir(row_tests) if name.startswith("test_")}
    mutant_test_names = {mutant.test.__name__ for mutant in MUTANTS}

    assert row_test_names == mutant_test_names
