"""Validation model for one row of a Spanish bank CSV export.

Each row from csv.DictReader is validated on its own, so one bad row becomes one entry in
the upload's error list instead of failing the whole file.

How one row flows through TransactionRow (full diagram: docs/LEARNING_LOG.md, session 2):

    {"Fecha": "03/10/2026", "Concepto": " CAFE SOL ", "Importe": "-3,50", "Saldo": ""}
          │                    │                       │                  │
     parse_bank_date     clean_description        parse_amount      parse_balance
          │                    │                       │                  │
     date(2026, 10, 3)     "CAFE SOL"         Decimal("-3.50")          None
          └────────────────────┴───────────┬───────────┴──────────────────┘
              ✓ TransactionRow (frozen)    or    ✗ ValidationError → row rejected
"""

# Imported as a module because the field is called `date`: `date: date` inside the class
# would let the field name shadow the type.
import datetime as dt
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict, Field, field_validator

# The bank exports dd/mm/yyyy only. Accepting other formats would let a swapped day and
# month (03/10 vs 10/03) slip in silently.
BANK_DATE_FORMAT = "%d/%m/%Y"


def parse_spanish_decimal(value: object, field_name: str) -> Decimal:
    """Parse a Spanish-formatted number such as '-2.100,35' into an exact Decimal.

    Shared by amount and balance so both follow the same rules; two copies of this logic
    would drift apart the first time one of them gets a bug fix.

    Args:
        value: Raw CSV cell, or an already-parsed Decimal when rows are built in code.
        field_name: Used in the error message, so the upload report names the bad column.

    Returns:
        The exact decimal value.

    Raises:
        ValueError: If the value is not a finite number. Always ValueError, because
            Pydantic only turns ValueError into a validation error; any other exception
            would crash the whole upload instead of rejecting one row.
    """
    if isinstance(value, Decimal):
        return value
    if not isinstance(value, str):
        # csv.DictReader yields None when a row has fewer cells than the header.
        raise ValueError(f"invalid {field_name} '{value}'")

    # Remove thousands dots BEFORE turning the decimal comma into a dot. In the other order,
    # "2.100,00" becomes "2.100.00" and the two kinds of dot can't be told apart.
    # Limitation: a dot-decimal value like "1.5" would read as 15; this bank never sends one.
    normalized = value.strip().replace(".", "").replace(",", ".")
    try:
        # Built from the string so the digits stay exact. Going through float first would
        # bake in binary rounding: Decimal(0.1) is 0.1000000000000000055511151231257827...
        number = Decimal(normalized)
    except InvalidOperation as exc:
        # Decimal raises InvalidOperation (an ArithmeticError, not a ValueError), which
        # Pydantic would let escape as a crash.
        raise ValueError(f"invalid {field_name} '{value}'") from exc

    # Decimal happily parses "NaN" and "Infinity", which are not amounts of money.
    if not number.is_finite():
        raise ValueError(f"invalid {field_name} '{value}'")
    return number


class TransactionRow(BaseModel):
    """One validated bank transaction, mapped from the bank's Spanish headers."""

    # validate_by_name: rows also build from English names (tests, DB reads) with no
    # translation step; aliases still let DictReader rows go straight in.
    # frozen: a row feeds the duplicate hash (D-006), so it must not change after validation.
    model_config = ConfigDict(validate_by_name=True, frozen=True)

    date: dt.date = Field(alias="Fecha")
    description: str = Field(alias="Concepto")
    amount: Decimal = Field(alias="Importe")
    # Optional because only some bank exports include a Saldo column (D-006).
    balance: Decimal | None = Field(default=None, alias="Saldo")

    @field_validator("date", mode="before")
    @classmethod
    def parse_bank_date(cls, value: object) -> dt.date:
        """Parse dd/mm/yyyy text into a date, leaving already-typed dates untouched.

        mode="before" runs on the raw cell, ahead of Pydantic's own date parser, which would
        accept ISO dates and replace our error message with its own.
        """
        if isinstance(value, dt.date):
            return value
        if not isinstance(value, str):
            raise ValueError(f"invalid date '{value}'")
        try:
            return dt.datetime.strptime(value.strip(), BANK_DATE_FORMAT).date()
        except ValueError as exc:
            # strptime rejects impossible dates like 31/02 as well as wrong formats.
            raise ValueError(f"invalid date '{value}'") from exc

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: object) -> str:
        """Strip padding and reject empty descriptions.

        Stripping stops 'CAFE SOL' and 'CAFE SOL  ' from becoming two merchants. Inner
        spacing is kept as the bank wrote it; heavier normalization belongs to the duplicate
        hash, not to the stored text.
        """
        if not isinstance(value, str) or not value.strip():
            # A row without a description can't be categorized or deduplicated.
            raise ValueError("empty description")
        return value.strip()

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> Decimal:
        """Parse the Importe cell with Spanish number rules."""
        return parse_spanish_decimal(value, "amount")

    @field_validator("balance", mode="before")
    @classmethod
    def parse_balance(cls, value: object) -> Decimal | None:
        """Parse the optional Saldo cell; a blank cell means the balance is unknown.

        Blank becomes None rather than an error: a missing balance doesn't make the
        transaction itself invalid, and the duplicate hash still has the occurrence count
        to fall back on for that row (D-006).
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return parse_spanish_decimal(value, "balance")
