"""Due date sequence generation for loan repayment schedules.

Produces an ordered sequence of (period_start, due_date) pairs for a loan,
handling month-end anchor day preservation across months of varying length.
"""

from __future__ import annotations

import calendar
from datetime import date

from loantrace.models.loan import FrequencyCode


def _add_months(anchor_day: int, year: int, month: int, months: int) -> date:
    """Return the date that is ``months`` months after the given year/month.

    The day is capped to the last valid day of the target month so that a
    January 31 anchor rolls to February 28 (or 29) rather than raising.

    Args:
        anchor_day: The fixed day-of-month for this schedule (e.g. 31).
        year: Year of the base period.
        month: Month of the base period.
        months: Number of months to advance.

    Returns:
        The due date in the target month.
    """
    total_months = month - 1 + months
    target_year = year + total_months // 12
    target_month = total_months % 12 + 1
    target_day = min(anchor_day, calendar.monthrange(target_year, target_month)[1])
    return date(target_year, target_month, target_day)


def generate_schedule_dates(
    value_date: date,
    installment_start_date: date | None,
    tenor_months: int,
    payment_cycle: FrequencyCode,
) -> tuple[tuple[date, date], ...]:
    """Generate the sequence of (period_start, due_date) pairs for a loan.

    The anchor day is derived from ``installment_start_date`` if supplied,
    otherwise from ``value_date``. It is held fixed for the life of the
    schedule so that month-end dates roll correctly (e.g. Jan 31 → Feb 28 →
    Mar 31) rather than drifting to the shortest month in the sequence.

    Args:
        value_date: Disbursement date — always the start of period 1.
        installment_start_date: Explicit first due date. If ``None``, the
            first due date is derived by adding one payment cycle to
            ``value_date``.
        tenor_months: Total loan term in months.
        payment_cycle: Monthly or quarterly payment frequency.

    Returns:
        Tuple of ``(period_start, due_date)`` pairs, one per period, in
        chronological order.
    """
    cycle_months = 1 if payment_cycle is FrequencyCode.MONTHLY else 3
    num_periods = tenor_months // cycle_months

    if installment_start_date is not None:
        first_due = installment_start_date
        anchor_day = installment_start_date.day
    else:
        anchor_day = value_date.day
        first_due = _add_months(
            anchor_day, value_date.year, value_date.month, cycle_months
        )

    periods: list[tuple[date, date]] = []
    period_start = value_date

    for i in range(num_periods):
        due_date = _add_months(
            anchor_day, first_due.year, first_due.month, i * cycle_months
        )
        periods.append((period_start, due_date))
        period_start = due_date

    return tuple(periods)
