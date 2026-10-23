"""Acceptance tests for the duplicate hash (D-006): keep real repeats, skip re-uploads."""

import datetime as dt
from decimal import Decimal

from finance_api.db.dedupe import dedupe_hashes
from finance_api.ingest.schemas import TransactionRow


def make_row(
    description: str = "CAFE SOL BARCELONA",
    amount: str = "-3.50",
    balance: str | None = None,
) -> TransactionRow:
    """Build a validated row with defaults, so each test changes only one field."""
    return TransactionRow(
        date=dt.date(2026, 10, 6),
        description=description,
        amount=Decimal(amount),
        balance=None if balance is None else Decimal(balance),
    )


def test_identical_rows_in_one_file_get_different_hashes() -> None:
    """Two real coffees on the same day are occurrence 1 and 2, so both are kept."""
    first, second = dedupe_hashes([make_row(), make_row()])

    assert first != second


def test_same_file_twice_gives_same_hashes() -> None:
    """A re-upload must produce exactly the hashes already stored, so it is skipped."""
    rows = [make_row(), make_row(), make_row(description="RECIBO ENDESA ENERGIA")]

    assert dedupe_hashes(rows) == dedupe_hashes(list(rows))


def test_case_and_inner_spacing_do_not_change_the_hash() -> None:
    """'CAFE  SOL' and 'cafe sol' are the same merchant written two ways by the bank."""
    assert dedupe_hashes([make_row("CAFE  SOL")]) == dedupe_hashes([make_row("cafe sol")])


def test_trailing_zeros_do_not_change_the_hash() -> None:
    """Decimal('-3.5') and Decimal('-3.50') are the same amount of money."""
    assert dedupe_hashes([make_row(amount="-3.5")]) == dedupe_hashes([make_row(amount="-3.50")])


def test_different_amount_gives_different_hash() -> None:
    """Same café, same day, different price: two different transactions."""
    assert dedupe_hashes([make_row(amount="-3.50")]) != dedupe_hashes([make_row(amount="-4.50")])


def test_balance_is_part_of_the_hash_when_present() -> None:
    """With Saldo, identical purchases differ by balance even across files (D-006 option C)."""
    with_first = dedupe_hashes([make_row(balance="100.00")])
    with_second = dedupe_hashes([make_row(balance="96.50")])

    assert with_first != with_second


def test_occurrence_counts_only_identical_rows() -> None:
    """A different row in between must not shift the count of the identical ones."""
    cafe = make_row()
    endesa = make_row(description="RECIBO ENDESA ENERGIA")

    together = dedupe_hashes([cafe, endesa, cafe])
    apart = dedupe_hashes([cafe, cafe])

    assert [together[0], together[2]] == apart


def test_fields_cannot_run_together() -> None:
    """Without a separator, 'CAFE SOL' + '-3.5' and 'CAFE SOL-3.' + '5' are the same text."""
    plain = dedupe_hashes([make_row("CAFE SOL", amount="-3.5")])
    shifted = dedupe_hashes([make_row("CAFE SOL-3.", amount="5")])

    assert plain != shifted


def test_hash_is_sha256_hex() -> None:
    """64 hex characters: fits the String(64) UNIQUE column exactly."""
    (digest,) = dedupe_hashes([make_row()])

    assert len(digest) == 64
    assert int(digest, 16) >= 0
