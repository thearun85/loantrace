"""Tests for loantrace.engine.dates."""

from __future__ import annotations

from datetime import date

from loantrace.engine.dates import _add_months, generate_schedule_dates
from loantrace.models.loan import FrequencyCode

# -------------------------------------------------------------------------
# _add_months
# -------------------------------------------------------------------------


class TestAddMonths:
    def test_standard_month(self) -> None:
        # Jan 15 + 1 month = Feb 15
        assert _add_months(15, 2026, 1, 1) == date(2026, 2, 15)

    def test_year_boundary(self) -> None:
        # Dec 1 + 1 month = Jan 1 next year
        assert _add_months(1, 2026, 12, 1) == date(2027, 1, 1)

    def test_multi_month_advance(self) -> None:
        # Jan 1 + 3 months = Apr 1
        assert _add_months(1, 2026, 1, 3) == date(2026, 4, 1)

    def test_month_end_anchor_short_month(self) -> None:
        # Anchor 31, Jan + 1 month → Feb has 28 days in 2026 — cap to 28
        assert _add_months(31, 2026, 1, 1) == date(2026, 2, 28)

    def test_month_end_anchor_recovers(self) -> None:
        # Anchor 31, Jan + 2 months → Mar has 31 days — full anchor restored
        assert _add_months(31, 2026, 1, 2) == date(2026, 3, 31)

    def test_month_end_anchor_leap_february(self) -> None:
        # Anchor 31, Jan 2028 + 1 month → Feb 2028 is leap — cap to 29
        assert _add_months(31, 2028, 1, 1) == date(2028, 2, 29)

    def test_anchor_30_in_february(self) -> None:
        # Anchor 30, Jan + 1 month → Feb 2026 has 28 days — cap to 28
        assert _add_months(30, 2026, 1, 1) == date(2026, 2, 28)

    def test_zero_months(self) -> None:
        # Adding 0 months returns the same month
        assert _add_months(15, 2026, 6, 0) == date(2026, 6, 15)

    def test_twelve_months(self) -> None:
        # 12 months lands on same date next year
        assert _add_months(15, 2026, 1, 12) == date(2027, 1, 15)


# -------------------------------------------------------------------------
# generate_schedule_dates — monthly, derived first due date
# -------------------------------------------------------------------------


class TestGenerateScheduleDatesMonthlyDerived:
    def test_period_count(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 1),
            installment_start_date=None,
            tenor_months=12,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        assert len(result) == 12

    def test_first_period_start_is_value_date(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 1),
            installment_start_date=None,
            tenor_months=12,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        assert result[0][0] == date(2026, 1, 1)

    def test_first_due_date_derived(self) -> None:
        # value_date Jan 1 → first due Feb 1
        result = generate_schedule_dates(
            value_date=date(2026, 1, 1),
            installment_start_date=None,
            tenor_months=12,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        assert result[0][1] == date(2026, 2, 1)

    def test_period_start_chains_from_previous_due(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 1),
            installment_start_date=None,
            tenor_months=3,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        # Period 2 start = period 1 due date
        assert result[1][0] == result[0][1]
        assert result[2][0] == result[1][1]

    def test_due_dates_sequential(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 1),
            installment_start_date=None,
            tenor_months=3,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        assert result[0][1] == date(2026, 2, 1)
        assert result[1][1] == date(2026, 3, 1)
        assert result[2][1] == date(2026, 4, 1)

    def test_returns_tuple_of_tuples(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 1),
            installment_start_date=None,
            tenor_months=1,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        assert isinstance(result, tuple)
        assert isinstance(result[0], tuple)


# -------------------------------------------------------------------------
# generate_schedule_dates — month-end anchor preservation
# -------------------------------------------------------------------------


class TestGenerateScheduleDatesMonthEnd:
    def test_jan31_anchor_preserved(self) -> None:
        # Jan 31 anchor: Feb → 28, Mar → 31, Apr → 30
        result = generate_schedule_dates(
            value_date=date(2026, 1, 31),
            installment_start_date=None,
            tenor_months=3,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        assert result[0][1] == date(2026, 2, 28)
        assert result[1][1] == date(2026, 3, 31)
        assert result[2][1] == date(2026, 4, 30)

    def test_jan31_anchor_leap_year(self) -> None:
        # Jan 31 2028: Feb 2028 is leap — cap to 29
        result = generate_schedule_dates(
            value_date=date(2028, 1, 31),
            installment_start_date=None,
            tenor_months=2,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        assert result[0][1] == date(2028, 2, 29)
        assert result[1][1] == date(2028, 3, 31)

    def test_anchor_does_not_drift(self) -> None:
        # If anchor drifted from Feb 28, Mar and beyond would be wrong
        result = generate_schedule_dates(
            value_date=date(2026, 1, 31),
            installment_start_date=None,
            tenor_months=4,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        # Apr 30 — not Apr 28 (which would result from drifting to Feb 28 anchor)
        assert result[2][1] == date(2026, 4, 30)


# -------------------------------------------------------------------------
# generate_schedule_dates — explicit installment_start_date
# -------------------------------------------------------------------------


class TestGenerateScheduleDatesExplicitStart:
    def test_explicit_first_due_used(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 15),
            installment_start_date=date(2026, 2, 20),
            tenor_months=3,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        assert result[0][1] == date(2026, 2, 20)

    def test_anchor_taken_from_explicit_start(self) -> None:
        # installment_start_date day=20, subsequent dues anchor to 20
        result = generate_schedule_dates(
            value_date=date(2026, 1, 15),
            installment_start_date=date(2026, 2, 20),
            tenor_months=3,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        assert result[1][1] == date(2026, 3, 20)
        assert result[2][1] == date(2026, 4, 20)

    def test_period_start_is_value_date_for_period_1(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 15),
            installment_start_date=date(2026, 2, 20),
            tenor_months=2,
            payment_cycle=FrequencyCode.MONTHLY,
        )
        assert result[0][0] == date(2026, 1, 15)


# -------------------------------------------------------------------------
# generate_schedule_dates — quarterly
# -------------------------------------------------------------------------


class TestGenerateScheduleDatesQuarterly:
    def test_period_count(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 1),
            installment_start_date=None,
            tenor_months=12,
            payment_cycle=FrequencyCode.QUARTERLY,
        )
        assert len(result) == 4

    def test_first_due_is_three_months_out(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 1),
            installment_start_date=None,
            tenor_months=12,
            payment_cycle=FrequencyCode.QUARTERLY,
        )
        assert result[0][1] == date(2026, 4, 1)

    def test_due_dates_three_months_apart(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 1),
            installment_start_date=None,
            tenor_months=12,
            payment_cycle=FrequencyCode.QUARTERLY,
        )
        assert result[1][1] == date(2026, 7, 1)
        assert result[2][1] == date(2026, 10, 1)
        assert result[3][1] == date(2027, 1, 1)

    def test_period_start_chains(self) -> None:
        result = generate_schedule_dates(
            value_date=date(2026, 1, 1),
            installment_start_date=None,
            tenor_months=12,
            payment_cycle=FrequencyCode.QUARTERLY,
        )
        assert result[1][0] == result[0][1]
        assert result[2][0] == result[1][1]
