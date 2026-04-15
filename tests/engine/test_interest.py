"""Tests for loantrace.engine.interest._resolve_days_in_period."""

from __future__ import annotations

from datetime import date

from loantrace.engine.interest import _resolve_days_in_period
from loantrace.models.loan import DaysInMonth


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
