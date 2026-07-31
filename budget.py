from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Sequence


@dataclass
class ExpenseRow:
    id: int
    date: date
    amount: int
    category: str
    description: str
    running_balance: int = 0


@dataclass
class DayState:
    date: date
    budget: int
    carry_in: int
    start_available: int
    expenses: list[ExpenseRow] = field(default_factory=list)
    spent: int = 0
    end_balance: int = 0
    eod_remainder: int = 0
    carry_out: int = 0
    saved: int = 0


def compute_days(
    expenses: Sequence,
    daily_budget: int,
    *,
    today: date | None = None,
    extra_dates: Sequence[date] | None = None,
) -> list[DayState]:
    """Compute daily balances with overspend carry to the next calendar day."""
    today = today or date.today()
    by_date: dict[date, list] = {}
    for expense in expenses:
        by_date.setdefault(expense.date, []).append(expense)

    anchors = set(by_date)
    if extra_dates:
        anchors.update(extra_dates)
    if not anchors:
        return [
            DayState(
                date=today,
                budget=daily_budget,
                carry_in=0,
                start_available=daily_budget,
                end_balance=daily_budget,
                eod_remainder=daily_budget,
            )
        ]

    start = min(anchors)
    end = max(today, max(anchors))

    days: list[DayState] = []
    carry = 0
    current = start
    while current <= end:
        day_expenses = sorted(by_date.get(current, []), key=lambda e: e.id)
        start_available = daily_budget - carry
        balance = start_available
        rows: list[ExpenseRow] = []
        spent = 0
        for expense in day_expenses:
            balance -= expense.amount
            spent += expense.amount
            rows.append(
                ExpenseRow(
                    id=expense.id,
                    date=expense.date,
                    amount=expense.amount,
                    category=expense.category,
                    description=expense.description or "",
                    running_balance=balance,
                )
            )

        rows.reverse()

        eod_remainder = max(0, balance)
        carry_out = max(0, -balance)
        days.append(
            DayState(
                date=current,
                budget=daily_budget,
                carry_in=carry,
                start_available=start_available,
                expenses=rows,
                spent=spent,
                end_balance=balance,
                eod_remainder=eod_remainder,
                carry_out=carry_out,
            )
        )
        carry = carry_out
        current += timedelta(days=1)

    return days
