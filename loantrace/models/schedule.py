"""Output models for a generated loan repayment schedule.

These models are immutable. All fields are populated by the engine
and must not be modified after construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class ComponentType(StrEnum):
    """Which component of the instalment a schedule row represents."""

    CAPITAL = "capital"
    INTEREST = "interest"


# -------------------------------------------------------------------------
# Calculation trace
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class CompCalc:
    """Full calculation trace for one accrual period within an interest row.

    Carries every value needed to independently verify the interest figure:
    run the formula with these inputs and you must get interest_gross.

    Attributes:
        start_date: First day of this accrual period.
        end_date: Last day of this accrual period (exclusive upper bound).
        principal_expected: Outstanding principal at the start of the period.
            Does not change mid-period.
        interest_rate: Annual rate applied for this period as a decimal
            fraction (e.g. Decimal('0.0525') for 5.25%).
        days_in_year: Resolved day-count denominator for this period —
            365, 360, or 366 for a leap year under ACTUAL convention.
        days_in_period: Actual number of days in this accrual period,
            after applying the days-in-month convention from LoanRequest.
        interest_gross: Unrounded result of
            principal_expected * interest_rate * days_in_period / days_in_year.
        interest_rounded: interest_gross rounded to 2 dp using ROUND_HALF_UP.
        interest_delta: Rounding effect — interest_rounded minus interest_gross.
    """

    start_date: date
    end_date: date
    principal_expected: Decimal
    interest_rate: Decimal
    days_in_year: int
    days_in_period: int
    interest_gross: Decimal
    interest_rounded: Decimal
    interest_delta: Decimal


# -------------------------------------------------------------------------
# Schedule row
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class Schedule:
    """One component row in the repayment schedule.

    A single instalment period produces two rows: one CAPITAL and one INTEREST.
    For INTEREST_ONLY loans, the CAPITAL row is omitted.

    Attributes:
        seq_no: Row sequence number, starting at 1.
        component: Whether this row represents a capital or interest component.
        start_date: First day of the period (previous due date, unadjusted).
        due_date: Payment due date for this period.
        amount_due: Total amount due for this component this period.
        calc: Accrual breakdown — populated for INTEREST rows only, None for
            CAPITAL rows. Contains one entry per rate sub-period.
    """

    seq_no: int
    component: ComponentType
    start_date: date
    due_date: date
    amount_due: Decimal
    calc: tuple[CompCalc, ...] | None = None  # INTEREST rows only
