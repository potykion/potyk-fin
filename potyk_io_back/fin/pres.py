from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func, select

from potyk_io_back.core.db import db
from potyk_io_back.fin.budget import compute_days
from potyk_io_back.fin.entities import Expense, Saving, get_settings
from potyk_io_back.fin.forms import BudgetForm, DeleteForm, ExpenseForm, SavingForm

bp = Blueprint("fin", __name__, url_prefix="/fin")


def flash_form_errors(form) -> None:
    for messages in form.errors.values():
        for message in messages:
            flash(message, "error")


def is_htmx() -> bool:
    return request.headers.get("HX-Request") == "true"


def index_context(
    *,
    open_panel: str | None = None,
    expense_form: ExpenseForm | None = None,
    saving_form: SavingForm | None = None,
    budget_form: BudgetForm | None = None,
) -> dict:
    settings = get_settings()
    expenses = db.session.scalars(
        select(Expense).order_by(Expense.date, Expense.id)
    ).all()
    savings = db.session.scalars(
        select(Saving).order_by(Saving.date.desc(), Saving.id.desc())
    ).all()
    categories = db.session.scalars(
        select(Expense.category).distinct().order_by(Expense.category)
    ).all()

    days = compute_days(
        expenses,
        settings.daily_budget,
        extra_dates=[s.date for s in savings],
    )
    saved_by_date: dict[date, int] = {}
    for s in savings:
        saved_by_date[s.date] = saved_by_date.get(s.date, 0) + s.amount
    for d in days:
        d.saved = saved_by_date.get(d.date, 0)

    days_desc = list(reversed(days))
    today = date.today()
    today_state = next((d for d in days if d.date == today), None)
    total_saved = db.session.scalar(select(func.coalesce(func.sum(Saving.amount), 0))) or 0
    auto_remainder_total = sum(d.eod_remainder for d in days if d.date < today)

    if budget_form is None:
        budget_form = BudgetForm(data={"daily_budget": settings.daily_budget})

    return {
        "settings": settings,
        "days": days_desc,
        "today": today,
        "today_state": today_state,
        "savings": savings,
        "total_saved": total_saved,
        "auto_remainder_total": auto_remainder_total,
        "categories": categories,
        "expense_form": expense_form or ExpenseForm(),
        "saving_form": saving_form or SavingForm(),
        "budget_form": budget_form,
        "delete_form": DeleteForm(),
        "open_panel": open_panel,
    }


def render_index(**kwargs):
    return render_template("index.html", **index_context(**kwargs))


@bp.route("/")
@login_required
def index():
    return render_index()


@bp.post("/expenses")
@login_required
def add_expense():
    form = ExpenseForm()
    if not form.validate_on_submit():
        if is_htmx():
            ctx = index_context(open_panel="expense", expense_form=form)
            return render_template("partials/_expense_form.html", **ctx)
        flash_form_errors(form)
        return render_index(open_panel="expense", expense_form=form), 400

    expense = Expense(
        date=form.date.data,
        amount=form.amount.data,
        category=form.category.data.strip(),
        description=(form.description.data or "").strip(),
    )
    db.session.add(expense)
    db.session.commit()

    if is_htmx():
        fresh = ExpenseForm(
            formdata=None,
            date=expense.date,
        )
        ctx = index_context(expense_form=fresh)
        return render_template("partials/_expense_added.html", **ctx)

    flash("Трата добавлена", "success")
    return redirect(url_for("fin.index"))


@bp.post("/expenses/<int:expense_id>/delete")
@login_required
def delete_expense(expense_id: int):
    form = DeleteForm()
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect(url_for("fin.index"))

    expense = db.session.get(Expense, expense_id)
    if expense is None:
        flash("Трата не найдена", "error")
        return redirect(url_for("fin.index"))
    db.session.delete(expense)
    db.session.commit()
    flash("Трата удалена", "success")
    return redirect(url_for("fin.index"))


@bp.post("/savings")
@login_required
def add_saving():
    form = SavingForm()
    if not form.validate_on_submit():
        flash_form_errors(form)
        return render_index(open_panel="saving", saving_form=form), 400

    db.session.add(
        Saving(
            date=form.date.data,
            amount=form.amount.data,
            note=(form.note.data or "").strip(),
        )
    )
    db.session.commit()
    flash("Сейв зафиксирован", "success")
    return redirect(url_for("fin.index"))


@bp.post("/savings/<int:saving_id>/delete")
@login_required
def delete_saving(saving_id: int):
    form = DeleteForm()
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect(url_for("fin.index"))

    saving = db.session.get(Saving, saving_id)
    if saving is None:
        flash("Сейв не найден", "error")
        return redirect(url_for("fin.index"))
    db.session.delete(saving)
    db.session.commit()
    flash("Сейв удалён", "success")
    return redirect(url_for("fin.index"))


@bp.post("/settings/budget")
@login_required
def update_budget():
    form = BudgetForm()
    if not form.validate_on_submit():
        flash_form_errors(form)
        return render_index(open_panel="budget", budget_form=form), 400

    settings = get_settings()
    settings.daily_budget = form.daily_budget.data
    db.session.commit()
    flash("Бюджет на день обновлён", "success")
    return redirect(url_for("fin.index"))
