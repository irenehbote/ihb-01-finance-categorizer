"""Duplicate hash for transactions: same row re-uploaded = same hash (D-006).

06/10 · CAFE SOL · -3,50   ──▶ key + occurrence 1 ──sha256──▶ hash A
06/10 · CAFE SOL · -3,50   ──▶ key + occurrence 2 ──sha256──▶ hash B   ✓ both kept
(same file again)          ──▶ A, B again                              ✓ both skipped
"""

import hashlib
from collections import Counter
from collections.abc import Sequence
from decimal import Decimal

from finance_api.ingest.schemas import TransactionRow

# ASCII unit separator: can't appear in a bank description, so fields can't run together
# ("AB" + "C" and "A" + "BC" would otherwise hash the same).
FIELD_SEPARATOR = "\x1f"


def normalize_description(description: str) -> str:
    """Casefold and collapse inner spaces, so the bank's spacing or case can't split a row.

    Only used for the hash: the stored description keeps the bank's original text.
    Digits are kept on purpose; card or receipt numbers can be what tells two rows apart.
    """
    return " ".join(description.casefold().split())


def normalize_amount(amount: Decimal | None) -> str:
    """Write an amount without trailing zeros, so -3.5 and -3.50 hash the same."""
    if amount is None:
        return ""
    # format "f" avoids normalize()'s exponent form (2.1E+3 for 2100).
    return format(amount.normalize(), "f")


def dedupe_hashes(rows: Sequence[TransactionRow]) -> list[str]:
    """Return one sha256 hash per row, in order, counting identical rows within the file.

    The occurrence number is what keeps two real, identical purchases apart: the first gets
    1, the second 2. A re-upload of the same file recounts the same way, so it reproduces
    the same hashes and the UNIQUE column skips them.
    """
    seen: Counter[str] = Counter()
    hashes: list[str] = []
    for row in rows:
        key = FIELD_SEPARATOR.join(
            [
                row.date.isoformat(),
                normalize_description(row.description),
                normalize_amount(row.amount),
                # Saldo is part of the key when the export has it (D-006 option C).
                normalize_amount(row.balance),
            ]
        )
        seen[key] += 1
        payload = f"{key}{FIELD_SEPARATOR}{seen[key]}"
        hashes.append(hashlib.sha256(payload.encode("utf-8")).hexdigest())
    return hashes
