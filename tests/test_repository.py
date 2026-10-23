"""Acceptance tests for saving parsed rows to SQLite with duplicate skipping (D-005, D-006)."""

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session

from finance_api.db.models import Transaction
from finance_api.db.repository import make_engine, save_rows
from finance_api.ingest.parser import parse_bank_csv
from finance_api.ingest.schemas import TransactionRow

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def session() -> Iterator[Session]:
    """A fresh in-memory database per test, so tests never see each other's rows."""
    engine = make_engine("sqlite://")
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


def fixture_rows(name: str) -> list[TransactionRow]:
    """Parse a fixture the same way an upload would; its one bad row is dropped."""
    rows, _ = parse_bank_csv((FIXTURES / name).read_bytes())
    return rows


def test_first_upload_inserts_every_row(session: Session) -> None:
    """All 7 valid rows are stored, including both identical coffees."""
    result = save_rows(session, fixture_rows("bank_sample.csv"))

    assert (result.inserted, result.skipped) == (7, 0)
    assert len(session.scalars(select(Transaction)).all()) == 7


def test_same_file_twice_skips_every_row(session: Session) -> None:
    """A re-upload adds nothing and reports every row as skipped."""
    rows = fixture_rows("bank_sample.csv")
    save_rows(session, rows)

    result = save_rows(session, rows)

    assert (result.inserted, result.skipped) == (0, 7)
    assert len(session.scalars(select(Transaction)).all()) == 7


def test_overlapping_export_inserts_only_new_rows(session: Session) -> None:
    """Exporting 1-6 Oct, then the whole month, stores the 2nd coffee and later rows once."""
    rows = fixture_rows("bank_sample.csv")
    save_rows(session, rows[:3])  # Mercadona, nómina, first coffee

    result = save_rows(session, rows)

    assert (result.inserted, result.skipped) == (4, 3)


def test_amounts_round_trip_as_exact_decimals(session: Session) -> None:
    """What goes in as Decimal comes back as the same Decimal, not a float."""
    save_rows(session, fixture_rows("bank_sample_saldo.csv"))

    stored = session.scalars(select(Transaction).order_by(Transaction.id)).first()

    assert stored is not None
    assert stored.amount == Decimal("-42.35")
    assert stored.balance == Decimal("1457.65")


def test_amounts_are_stored_as_integer_cents(session: Session) -> None:
    """SQLite has no decimal type: integer cents keep SUM exact in SQL (D-013)."""
    save_rows(session, fixture_rows("bank_sample.csv"))

    kind, total = session.execute(
        text("SELECT typeof(amount), SUM(amount) FROM transactions")
    ).one()

    assert kind == "integer"
    assert total == 195246  # 2100.00 - 42.35 - 3.50 * 2 - 61.20 - 11.99 - 25.00, in cents


def test_more_than_two_decimals_is_refused_not_rounded(session: Session) -> None:
    """Silently rounding 0.005 would change my money; a loud error is safer."""
    row = fixture_rows("bank_sample.csv")[0].model_copy(update={"amount": Decimal("-1.005")})

    with pytest.raises(StatementError, match="more than 2 decimals"):
        save_rows(session, [row])


def test_database_itself_rejects_a_duplicate_hash(session: Session) -> None:
    """The UNIQUE constraint lives in the DB, not only in our code (D-006)."""
    save_rows(session, fixture_rows("bank_sample.csv")[:1])
    existing = session.scalars(select(Transaction)).one()
    copy = Transaction(
        date=existing.date,
        description=existing.description,
        amount=existing.amount,
        balance=existing.balance,
        dedupe_hash=existing.dedupe_hash,
    )

    session.add(copy)
    with pytest.raises(IntegrityError):
        session.flush()
