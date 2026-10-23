"""Save validated rows, letting the database skip duplicates (D-006, D-012).

rows ──dedupe_hashes──▶ one dict per row
     ──INSERT … ON CONFLICT (dedupe_hash) DO NOTHING RETURNING id──▶ SQLite
          ├──▶ new hash   ✓ inserted (id returned)
          └──▶ known hash ✓ skipped  (nothing returned)
"""

from collections.abc import Sequence
from typing import NamedTuple

from sqlalchemy import Engine, create_engine
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from finance_api.db.dedupe import dedupe_hashes
from finance_api.db.models import Base, Transaction
from finance_api.ingest.schemas import TransactionRow


class SaveResult(NamedTuple):
    """How many rows of one upload were new and how many were already stored."""

    inserted: int
    skipped: int


def make_engine(url: str) -> Engine:
    """Create the engine and any missing tables.

    create_all only adds tables that don't exist yet; it never alters or drops them, so it
    is safe on every start. Real migrations (Alembic) wait until the schema first changes.
    """
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine


def save_rows(session: Session, rows: Sequence[TransactionRow]) -> SaveResult:
    """Insert rows whose hash is new and count the rest as skipped.

    Does not commit: the caller (the upload endpoint) owns the transaction, so a failure
    later in the same request can roll back the whole upload.
    """
    if not rows:
        # An empty VALUES list is invalid SQL, and there is nothing to report anyway.
        return SaveResult(inserted=0, skipped=0)

    values = [
        {
            "date": row.date,
            "description": row.description,
            "amount": row.amount,
            "balance": row.balance,
            "dedupe_hash": digest,
        }
        for row, digest in zip(rows, dedupe_hashes(rows), strict=True)
    ]
    # The database checks the UNIQUE column and skips known hashes in the same statement,
    # so there is no gap between "check" and "insert" for a second upload to slip through.
    statement = (
        sqlite_insert(Transaction)
        .values(values)
        .on_conflict_do_nothing(index_elements=["dedupe_hash"])
        .returning(Transaction.id)
    )
    inserted = len(session.execute(statement).all())
    return SaveResult(inserted=inserted, skipped=len(rows) - inserted)
