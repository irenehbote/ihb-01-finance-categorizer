"""SQLAlchemy table for stored transactions (D-005).

TransactionRow (Decimal)              transactions table
───────────────────────────           ─────────────────────────────────
amount  Decimal("-3.50")   ──Cents──▶ amount  -350        INTEGER
balance Decimal | None     ──Cents──▶ balance  NULL/int   INTEGER
dedupe_hash (from dedupe.py)  ──────▶ dedupe_hash  UNIQUE  ✓ DB rejects repeats
"""

import datetime as dt
from decimal import Decimal

from sqlalchemy import BigInteger, Date, Dialect, String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

CENTS_PER_UNIT = 100


class Cents(TypeDecorator[Decimal]):
    """Store a Decimal amount of euros as an integer number of cents (D-013).

    SQLite has no decimal type: SQLAlchemy's Numeric is stored as REAL there, so
    SUM(0.10 + 0.20) in SQL returns 0.30000000000000004 (checked). Integer cents are
    exact in every database and still read back as Decimal in Python.
    """

    impl = BigInteger
    cache_ok = True  # stateless, so SQLAlchemy may reuse compiled statements

    def process_bind_param(self, value: Decimal | None, dialect: Dialect) -> int | None:
        """Convert euros to cents on the way into the database."""
        if value is None:
            return None
        cents = value * CENTS_PER_UNIT
        if cents != cents.to_integral_value():
            # Refuse instead of rounding: rounding would silently change a stored amount.
            raise ValueError(f"amount {value} has more than 2 decimals")
        return int(cents)

    def process_result_value(self, value: int | None, dialect: Dialect) -> Decimal | None:
        """Convert cents back to euros, always with 2 decimal places."""
        if value is None:
            return None
        return Decimal(value).scaleb(-2)


class Base(DeclarativeBase):
    """Shared metadata for every table, so create_all builds them together."""


class Transaction(Base):
    """One stored bank transaction. Category columns arrive with Features 1.3 and 1.4."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String)
    amount: Mapped[Decimal] = mapped_column(Cents)
    balance: Mapped[Decimal | None] = mapped_column(Cents, nullable=True)
    # sha256 hex is always 64 characters. unique=True puts the rule in the database, so
    # even code that skips save_rows can't store the same transaction twice (D-006).
    dedupe_hash: Mapped[str] = mapped_column(String(64), unique=True)
