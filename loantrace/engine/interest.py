from datetime import date

from loantrace.models.loan import DaysInMonth


def _resolve_days_in_period(
    start_date: date,
    end_date: date,
    convention: DaysInMonth,
) -> int:
    """Return the number of days in an accrual period under the given convention.

    This is the numerator in the interest formula:
        interest = principal * rate * days_in_period / days_in_year

    Args:
        start_date: First day of the accrual period (inclusive).
        end_date: Last day of the accrual period (exclusive upper bound).
        convention: Day-count numerator convention from the loan request.

    Returns:
        Integer day count to use in the interest calculation.
    """
    if convention is DaysInMonth.ACTUAL:
        # Use the real calendar distance between the two dates.
        return (end_date - start_date).days

    y1, m1, d1 = start_date.year, start_date.month, start_date.day
    y2, m2, d2 = end_date.year, end_date.month, end_date.day

    if convention is DaysInMonth.EURO_30:
        # ISDA 30E/360: cap both day components at 30 unconditionally.
        # February, 31-day months, and end-of-month dates are all treated
        # as 30 without exception.
        d1 = min(d1, 30)
        d2 = min(d2, 30)

    elif convention is DaysInMonth.US_30:
        # ISDA 30/360 US: cap D1 at 30, then cap D2 only if D1 was month-end.
        # This normalises end-of-month to end-of-month (e.g. 31 Jan → 28 Feb
        # is treated as a full 30-day month) but leaves mid-month D2 values
        # untouched when D1 is not at month-end.
        if d1 == 31:
            d1 = 30
        if d2 == 31 and d1 == 30:
            # D1 was 30 or 31 (now 30) — treat D2 as end-of-month too.
            d2 = 30

    # Shared formula for both 30-day conventions.
    return 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
