"""Tests for loantrace.engine.interest."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from loantrace.engine.interest import (
    _calculate,
    _resolve_days_in_period,
    _resolve_days_in_year,
    process_accrual,
)
from loantrace.models.loan import DaysInMonth, DaysInYear


class TestResolveDaysInPeriodActual:
    def test_january(self) -> None:
        # 31 calendar days
        assert (
            _resolve_days_in_period(
                date(2026, 1, 1), date(2026, 2, 1), DaysInMonth.ACTUAL
            )
            == 31
        )

    def test_february_non_leap(self) -> None:
        # 2026 is not a leap year
        assert (
            _resolve_days_in_period(
                date(2026, 2, 1), date(2026, 3, 1), DaysInMonth.ACTUAL
            )
            == 28
        )

    def test_february_leap(self) -> None:
        # 2028 is a leap year
        assert (
            _resolve_days_in_period(
                date(2028, 2, 1), date(2028, 3, 1), DaysInMonth.ACTUAL
            )
            == 29
        )

    def test_april(self) -> None:
        # 30 calendar days
        assert (
            _resolve_days_in_period(
                date(2026, 4, 1), date(2026, 5, 1), DaysInMonth.ACTUAL
            )
            == 30
        )


class TestResolveDaysInPeriodEuro30:
    def test_standard_month(self) -> None:
        # Jan 1 → Feb 1: D1=1, D2=1 — 30*(1) + (1-1) = 30
        assert (
            _resolve_days_in_period(
                date(2026, 1, 1), date(2026, 2, 1), DaysInMonth.EURO_30
            )
            == 30
        )

    def test_31st_start(self) -> None:
        # Jan 31 → Mar 31: D1=min(31,30)=30, D2=min(31,30)=30 — 30*(2) + (30-30) = 60
        assert (
            _resolve_days_in_period(
                date(2026, 1, 31), date(2026, 3, 31), DaysInMonth.EURO_30
            )
            == 60
        )

    def test_end_of_february(self) -> None:
        # Jan 31 → Feb 28: D1=30, D2=min(28,30)=28 — 30*(1) + (28-30) = 28
        assert (
            _resolve_days_in_period(
                date(2026, 1, 31), date(2026, 2, 28), DaysInMonth.EURO_30
            )
            == 28
        )

    def test_mid_month(self) -> None:
        # Jan 15 → Mar 15: D1=15, D2=15 — 30*(2) + (15-15) = 60
        assert (
            _resolve_days_in_period(
                date(2026, 1, 15), date(2026, 3, 15), DaysInMonth.EURO_30
            )
            == 60
        )

    def test_d2_31_capped_unconditionally(self) -> None:
        # Jan 15 → Mar 31: D1=15, D2=min(31,30)=30 — 30*(2) + (30-15) = 75
        # EURO_30 caps D2 regardless of D1 — contrast with US_30 below
        assert (
            _resolve_days_in_period(
                date(2026, 1, 15), date(2026, 3, 31), DaysInMonth.EURO_30
            )
            == 75
        )


class TestResolveDaysInPeriodUS30:
    def test_standard_month(self) -> None:
        # Jan 1 → Feb 1: D1=1, D2=1 — no adjustments — 30*(1) + (1-1) = 30
        assert (
            _resolve_days_in_period(
                date(2026, 1, 1), date(2026, 2, 1), DaysInMonth.US_30
            )
            == 30
        )

    def test_d1_31_caps_d1(self) -> None:
        # Jan 31 → Feb 28: D1=31→30, D2=28 (not 31) — 30*(1) + (28-30) = 28
        assert (
            _resolve_days_in_period(
                date(2026, 1, 31), date(2026, 2, 28), DaysInMonth.US_30
            )
            == 28
        )

    def test_d1_30_caps_d2_when_31(self) -> None:
        # Jan 30 → Mar 31: D1=30 (no change), D2=31 and D1==30 → D2=30
        # 30*(2) + (30-30) = 60
        assert (
            _resolve_days_in_period(
                date(2026, 1, 30), date(2026, 3, 31), DaysInMonth.US_30
            )
            == 60
        )

    def test_d1_mid_month_d2_31_not_capped(self) -> None:
        # Jan 15 → Mar 31: D1=15, D2=31 but D1 not month-end — D2 stays 31
        # 30*(2) + (31-15) = 76 — contrast with EURO_30 which gives 75
        assert (
            _resolve_days_in_period(
                date(2026, 1, 15), date(2026, 3, 31), DaysInMonth.US_30
            )
            == 76
        )

    def test_d1_31_and_d2_31(self) -> None:
        # Jan 31 → Mar 31: D1=31→30, D2=31 and D1==30 → D2=30
        # 30*(2) + (30-30) = 60
        assert (
            _resolve_days_in_period(
                date(2026, 1, 31), date(2026, 3, 31), DaysInMonth.US_30
            )
            == 60
        )


class TestResolveDaysInYear:
    def test_days_365(self) -> None:
        # Fixed — year and leap status are irrelevant
        assert _resolve_days_in_year(date(2026, 1, 1), DaysInYear.DAYS_365) == 365

    def test_days_360(self) -> None:
        assert _resolve_days_in_year(date(2026, 1, 1), DaysInYear.DAYS_360) == 360

    def test_actual_non_leap(self) -> None:
        # 2026 is not a leap year
        assert _resolve_days_in_year(date(2026, 6, 1), DaysInYear.ACTUAL) == 365

    def test_actual_leap(self) -> None:
        # 2028 is a leap year
        assert _resolve_days_in_year(date(2028, 6, 1), DaysInYear.ACTUAL) == 366

    def test_actual_uses_start_date_year(self) -> None:
        # Period spans year boundary — 2027 is not a leap year, so 365
        assert _resolve_days_in_year(date(2027, 12, 1), DaysInYear.ACTUAL) == 365

    def test_actual_century_non_leap(self) -> None:
        # 1900 is divisible by 100 but not 400 — not a leap year
        assert _resolve_days_in_year(date(1900, 1, 1), DaysInYear.ACTUAL) == 365

    def test_actual_400_year_leap(self) -> None:
        # 2000 is divisible by 400 — is a leap year
        assert _resolve_days_in_year(date(2000, 1, 1), DaysInYear.ACTUAL) == 366


class TestCalculate:
    def test_basic_interest(self) -> None:
        # 250000 * 0.0525 * 31 / 365 = 1114.726...  → 1114.73
        calc = _calculate(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            principal=Decimal("250000.00"),
            annual_rate=Decimal("0.0525"),
            days_in_period=31,
            days_in_year=365,
        )
        assert calc.interest_rounded == Decimal("1114.73")

    def test_gross_is_unrounded(self) -> None:
        calc = _calculate(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            principal=Decimal("250000.00"),
            annual_rate=Decimal("0.0525"),
            days_in_period=31,
            days_in_year=365,
        )
        assert calc.interest_gross != calc.interest_rounded

    def test_delta_is_rounded_minus_gross(self) -> None:
        calc = _calculate(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            principal=Decimal("250000.00"),
            annual_rate=Decimal("0.0525"),
            days_in_period=31,
            days_in_year=365,
        )
        assert calc.interest_delta == calc.interest_rounded - calc.interest_gross

    def test_fields_populated(self) -> None:
        calc = _calculate(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            principal=Decimal("250000.00"),
            annual_rate=Decimal("0.0525"),
            days_in_period=31,
            days_in_year=365,
        )
        assert calc.start_date == date(2026, 1, 1)
        assert calc.end_date == date(2026, 2, 1)
        assert calc.principal_expected == Decimal("250000.00")
        assert calc.interest_rate == Decimal("0.0525")
        assert calc.days_in_period == 31
        assert calc.days_in_year == 365

    def test_round_half_up(self) -> None:
        # Construct a case where ROUND_HALF_EVEN and ROUND_HALF_UP differ.
        # 1.125 → ROUND_HALF_UP = 1.13, ROUND_HALF_EVEN = 1.12
        # principal * rate * days / year = 1.125 exactly
        # 10000 * 0.045 * 1 / 400 = 1.125
        calc = _calculate(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            principal=Decimal("10000"),
            annual_rate=Decimal("0.045"),
            days_in_period=1,
            days_in_year=400,
        )
        assert calc.interest_rounded == Decimal("1.13")


class TestProcessAccrual:
    def test_returns_tuple(self) -> None:
        result = process_accrual(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            principal=Decimal("250000.00"),
            annual_rate=Decimal("0.0525"),
            days_in_month=DaysInMonth.ACTUAL,
            days_in_year=DaysInYear.ACTUAL,
        )
        assert isinstance(result, tuple)

    def test_phase_1_single_comp_calc(self) -> None:
        result = process_accrual(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            principal=Decimal("250000.00"),
            annual_rate=Decimal("0.0525"),
            days_in_month=DaysInMonth.ACTUAL,
            days_in_year=DaysInYear.ACTUAL,
        )
        assert len(result) == 1

    def test_correct_interest(self) -> None:
        # 250000 * 0.0525 * 31 / 365 = 1114.726... → 1114.73
        result = process_accrual(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            principal=Decimal("250000.00"),
            annual_rate=Decimal("0.0525"),
            days_in_month=DaysInMonth.ACTUAL,
            days_in_year=DaysInYear.ACTUAL,
        )
        assert result[0].interest_rounded == Decimal("1114.73")

    def test_days_resolved_correctly(self) -> None:
        result = process_accrual(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            principal=Decimal("250000.00"),
            annual_rate=Decimal("0.0525"),
            days_in_month=DaysInMonth.ACTUAL,
            days_in_year=DaysInYear.ACTUAL,
        )
        assert result[0].days_in_period == 31
        assert result[0].days_in_year == 365

    def test_euro_30_convention(self) -> None:
        # Jan period — EURO_30 gives 30 days not 31
        result = process_accrual(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            principal=Decimal("250000.00"),
            annual_rate=Decimal("0.0525"),
            days_in_month=DaysInMonth.EURO_30,
            days_in_year=DaysInYear.DAYS_360,
        )
        assert result[0].days_in_period == 30
        assert result[0].days_in_year == 360

    def test_comp_calc_dates_match_period(self) -> None:
        result = process_accrual(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
            principal=Decimal("250000.00"),
            annual_rate=Decimal("0.0525"),
            days_in_month=DaysInMonth.ACTUAL,
            days_in_year=DaysInYear.ACTUAL,
        )
        assert result[0].start_date == date(2026, 1, 1)
        assert result[0].end_date == date(2026, 2, 1)
