"""Tests for loantrace.models.loan"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from loantrace.models.loan import (
    DaysInMonth,
    DaysInYear,
    FrequencyCode,
    LoanRequest,
    LoanSummary,
    RateType,
    RepaymentType,
    ScheduleType,
)
from loantrace.models.schedule import (
    ComponentType,
    Schedule,
)

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

VALID: dict[str, Any] = {
    "loan_amount": Decimal("250000.00"),
    "interest_rate": Decimal("0.0525"),
    "tenor_months": 300,
    "value_date": date(2026, 1, 1),
    "payment_cycle": FrequencyCode.MONTHLY,
    "schedule_type": ScheduleType.AMORTISED_REDUCING,
    "repayment_type": RepaymentType.CAPITAL_AND_INTEREST,
}


def make(**overrides: Any) -> LoanRequest:  # noqa: ANN401 — test helper, no alternative to Any for **kwargs override pattern
    return LoanRequest(**{**VALID, **overrides})


# -------------------------------------------------------------------------
# LoanRequest
# -------------------------------------------------------------------------


class TestLoanRequestHappyPath:
    def test_construction(self) -> None:
        loan = make()
        assert loan.loan_amount == Decimal("250000.00")
        assert loan.interest_rate == Decimal("0.0525")
        assert loan.tenor_months == 300
        assert loan.value_date == date(2026, 1, 1)
        assert loan.payment_cycle == FrequencyCode.MONTHLY
        assert loan.schedule_type == ScheduleType.AMORTISED_REDUCING
        assert loan.repayment_type == RepaymentType.CAPITAL_AND_INTEREST

    def test_defaults(self) -> None:
        loan = make()
        assert loan.rate_type == RateType.FIXED
        assert loan.installment_start_date is None
        assert loan.days_in_year == DaysInYear.ACTUAL
        assert loan.days_in_month == DaysInMonth.ACTUAL

    def test_installment_start_date_supplied(self) -> None:
        loan = make(installment_start_date=date(2026, 4, 20))
        assert loan.installment_start_date == date(2026, 4, 20)

    def test_repayment_type_interest_only(self) -> None:
        loan = make(repayment_type=RepaymentType.INTEREST_ONLY)
        assert loan.repayment_type == RepaymentType.INTEREST_ONLY


class TestLoanRequestImmutability:
    def test_frozen(self) -> None:
        loan = make()
        with pytest.raises(FrozenInstanceError):
            loan.loan_amount = Decimal("500000.00")  # type: ignore[misc]


class TestLoanRequestEnum:
    def test_payment_cycle_monthly(self) -> None:
        loan = make(payment_cycle=FrequencyCode.MONTHLY)
        assert loan.payment_cycle == FrequencyCode.MONTHLY

    def test_payment_cycle_quarterly(self) -> None:
        loan = make(payment_cycle=FrequencyCode.QUARTERLY)
        assert loan.payment_cycle == FrequencyCode.QUARTERLY

    def test_schedule_type_amortised_reducing(self) -> None:
        loan = make(schedule_type=ScheduleType.AMORTISED_REDUCING)
        assert loan.schedule_type == ScheduleType.AMORTISED_REDUCING

    def test_schedule_type_simple(self) -> None:
        loan = make(schedule_type=ScheduleType.SIMPLE)
        assert loan.schedule_type == ScheduleType.SIMPLE

    def test_repayment_type_capital_and_interest(self) -> None:
        loan = make(repayment_type=RepaymentType.CAPITAL_AND_INTEREST)
        assert loan.repayment_type == RepaymentType.CAPITAL_AND_INTEREST

    def test_repayment_type_interest_only(self) -> None:
        loan = make(repayment_type=RepaymentType.INTEREST_ONLY)
        assert loan.repayment_type == RepaymentType.INTEREST_ONLY

    def test_rate_type_fixed(self) -> None:
        loan = make(rate_type=RateType.FIXED)
        assert loan.rate_type == RateType.FIXED

    def test_rate_type_variable(self) -> None:
        loan = make(rate_type=RateType.VARIABLE)
        assert loan.rate_type == RateType.VARIABLE

    def test_days_in_year_365(self) -> None:
        loan = make(days_in_year=DaysInYear.DAYS_365)
        assert loan.days_in_year == DaysInYear.DAYS_365

    def test_days_in_year_360(self) -> None:
        loan = make(days_in_year=DaysInYear.DAYS_360)
        assert loan.days_in_year == DaysInYear.DAYS_360

    def test_days_in_year_actual(self) -> None:
        loan = make(days_in_year=DaysInYear.ACTUAL)
        assert loan.days_in_year == DaysInYear.ACTUAL

    def test_days_in_month_euro_30(self) -> None:
        loan = make(days_in_month=DaysInMonth.EURO_30)
        assert loan.days_in_month == DaysInMonth.EURO_30

    def test_days_in_month_us_30(self) -> None:
        loan = make(days_in_month=DaysInMonth.US_30)
        assert loan.days_in_month == DaysInMonth.US_30

    def test_days_in_month_actual(self) -> None:
        loan = make(days_in_month=DaysInMonth.ACTUAL)
        assert loan.days_in_month == DaysInMonth.ACTUAL


# -------------------------------------------------------------------------
# LoanSummary
# -------------------------------------------------------------------------


class TestLoanSummaryHappyPath:
    def test_construction(self) -> None:
        loan = make()
        summary = LoanSummary(loan_request=loan, schedules=())
        assert summary.loan_request is loan
        assert summary.schedules == ()

    def test_with_schedules(self) -> None:
        loan = make()
        schedule = Schedule(
            seq_no=1,
            component=ComponentType.CAPITAL,
            start_date=date(2026, 1, 1),
            due_date=date(2026, 2, 1),
            amount_due=Decimal("1000.00"),
        )
        summary = LoanSummary(loan_request=loan, schedules=(schedule,))
        assert len(summary.schedules) == 1
        assert summary.schedules[0].component == ComponentType.CAPITAL


class TestLoanSummaryImmutability:
    def test_frozen(self) -> None:
        loan = make()
        summary = LoanSummary(loan_request=loan, schedules=())
        with pytest.raises(FrozenInstanceError):
            summary.loan_request.loan_amount = Decimal("500000.00")  # type: ignore[misc]
