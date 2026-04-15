"""Tests for loantrace.models.schedule."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from loantrace.models.schedule import (
    CompCalc,
    ComponentType,
    Schedule,
)

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

VALID_COMP_CALC: dict[str, Any] = {
    "start_date": date(2026, 1, 1),
    "end_date": date(2026, 2, 1),
    "principal_expected": Decimal("250000.00"),
    "interest_rate": Decimal("0.0525"),
    "days_in_year": 365,
    "days_in_period": 31,
    "interest_gross": Decimal("1118.15"),
    "interest_rounded": Decimal("1118.15"),
    "interest_delta": Decimal("0.00"),
}

VALID_SCHEDULE: dict[str, Any] = {
    "seq_no": 1,
    "component": ComponentType.CAPITAL,
    "start_date": date(2026, 1, 1),
    "due_date": date(2026, 2, 1),
    "amount_due": Decimal("1000.00"),
}


def make_comp_calc(**overrides: Any) -> CompCalc:  # noqa: ANN401 — test helper, no alternative to Any for **kwargs override pattern
    return CompCalc(**{**VALID_COMP_CALC, **overrides})


def make_schedule(**overrides: Any) -> Schedule:  # noqa: ANN401 — test helper, no alternative to Any for **kwargs override pattern
    return Schedule(**{**VALID_SCHEDULE, **overrides})


# -------------------------------------------------------------------------
# CompCalc
# -------------------------------------------------------------------------


class TestCompCalcHappyPath:
    def test_construction(self) -> None:
        calc = make_comp_calc()
        assert calc.start_date == date(2026, 1, 1)
        assert calc.end_date == date(2026, 2, 1)
        assert calc.principal_expected == Decimal("250000.00")
        assert calc.interest_rate == Decimal("0.0525")
        assert calc.days_in_year == 365
        assert calc.days_in_period == 31
        assert calc.interest_gross == Decimal("1118.15")
        assert calc.interest_rounded == Decimal("1118.15")
        assert calc.interest_delta == Decimal("0.00")


class TestCompCalcImmutability:
    def test_frozen(self) -> None:
        calc = make_comp_calc()
        with pytest.raises(FrozenInstanceError):
            calc.interest_rate = Decimal("0.0100")  # type: ignore[misc]


# -------------------------------------------------------------------------
# Schedule
# -------------------------------------------------------------------------


class TestScheduleHappyPath:
    def test_construction(self) -> None:
        row = make_schedule()
        assert row.seq_no == 1
        assert row.component is ComponentType.CAPITAL
        assert row.start_date == date(2026, 1, 1)
        assert row.due_date == date(2026, 2, 1)
        assert row.amount_due == Decimal("1000.00")
        assert row.calc is None

    def test_interest_row_with_calc(self) -> None:
        calc = make_comp_calc()
        row = make_schedule(component=ComponentType.INTEREST, calc=(calc,))
        assert row.component is ComponentType.INTEREST
        assert row.calc is not None
        assert len(row.calc) == 1
        assert row.calc[0] is calc

    def test_calc_default_is_none(self) -> None:
        row = make_schedule()
        assert row.calc is None

    def test_multiple_calc_periods(self) -> None:
        calc1 = make_comp_calc(start_date=date(2026, 1, 1), end_date=date(2026, 1, 10))
        calc2 = make_comp_calc(start_date=date(2026, 1, 10), end_date=date(2026, 2, 1))

        row = make_schedule(calc=(calc1, calc2))
        assert row.calc is not None
        assert len(row.calc) == 2


class TestScheduleImmutability:
    def test_frozen(self) -> None:
        row = make_schedule()
        with pytest.raises(FrozenInstanceError):
            row.due_date = date(2026, 3, 1)  # type: ignore[misc]
