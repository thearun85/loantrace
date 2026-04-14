"""Input model for a loan repayment schedule request.

Only fields required for Phase 1 are defined here.

 - Rate type       : Fixed and Variable
 - Payment cycle   : Monthly
 - Repayment types : Capital & Interest and Interest Only
 - Day count       : Actual / 365

No float values are accepted.
All monetary and rate inputs must be supplied as Decimal.
Floats and strings are rejected at the boundary. See ADR-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from .schedule import Schedule


class FrequencyCode(StrEnum):
    """How often an instalment is collected."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class RepaymentType(StrEnum):
    """What components are collected each period."""

    CAPITAL_AND_INTEREST = "capital_and_interest"
    INTEREST_ONLY = "interest_only"


class RateType(StrEnum):
    """Whether the interest rate is fixed for the term or variable."""

    FIXED = "fixed"
    VARIABLE = "variable"


class ScheduleType(StrEnum):
    """How instalment amounts are calculated over the loan term."""

    AMORTISED_REDUCING = (
        "amortised_reducing"  # Fixed EMI; principal/interest split varies
    )
    SIMPLE = (
        "simple"  # Fixed principal per period; interest varies on outstanding balance
    )


class DaysInYear(StrEnum):
    """Convention for the day-count denominator in interest calculations."""

    DAYS_365 = "365"  # Fixed 365-day year
    DAYS_360 = "360"  # Fixed 360-day year
    ACTUAL = "actual"  # Actual days in the year — 365 or 366 for leap years


class DaysInMonth(StrEnum):
    """Convention for counting days within an accrual period."""

    EURO_30 = "euro"  # Every month treated as 30 days (ISDA 30E/360)
    US_30 = "us"  # US 30/360 — adjusts 31st and end-of-February
    ACTUAL = "actual"  # Actual calendar days between period dates


# -------------------------------------------------------------------------
# Loan Request
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class LoanRequest:
    """Immutable input describing a loan for which a schedule is requested.

    Attributes:
        loan_amount: Sanctioned loan amount in currency units
            (e.g. Decimal('250000.00')).
        interest_rate: Annual interest rate as a decimal fraction, not a
            percentage (e.g. Decimal('0.0525') for 5.25%).
        tenor_months: Loan term in whole months (e.g. 300 for 25 years).
        value_date: Date the loan is initiated; the date of the first
            disbursement.
        payment_cycle: How often an instalment falls due.
        schedule_type: Calculation method — amortised reducing (fixed EMI)
            or simple (fixed principal, variable interest).
        repayment_type: Whether instalments cover capital + interest
            or interest only.
        rate_type: Whether the rate is fixed for the term or variable.
            Variable rate is Phase 2; defaults to FIXED.
        installment_start_date: First instalment due date. If None, derived
            from value_date plus one payment cycle (loan in arrears).
        days_in_year: Day-count denominator convention. Defaults to ACTUAL.
        days_in_month: Day-count numerator convention. Defaults to ACTUAL.
    """

    loan_amount: Decimal
    interest_rate: Decimal
    tenor_months: int
    value_date: date
    payment_cycle: FrequencyCode
    schedule_type: ScheduleType
    repayment_type: RepaymentType
    rate_type: RateType = RateType.FIXED
    installment_start_date: date | None = None
    days_in_year: DaysInYear = DaysInYear.ACTUAL
    days_in_month: DaysInMonth = DaysInMonth.ACTUAL


# -------------------------------------------------------------------------
# Loan Summary
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class LoanSummary:
    """Complete output for a schedule generation request.

    Pairs the original request with the generated schedule rows so the
    full calculation context is always available alongside the output.

    Attributes:
        loan_request: The original immutable input that produced this schedule.
        schedules: All schedule rows, ordered by seq_no. One CAPITAL and one
            INTEREST row per period for CAPITAL_AND_INTEREST loans; INTEREST
            rows only for INTEREST_ONLY loans.
    """

    loan_request: LoanRequest
    schedules: tuple[Schedule, ...]
