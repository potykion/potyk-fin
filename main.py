import os
from datetime import date

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, url_for
from flask_login import login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, select

load_dotenv()

from auth import setup_login
from budget import compute_days
from forms import BudgetForm, DeleteForm, ExpenseForm, SavingForm

db = SQLAlchemy()


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")


class Saving(db.Model):
    __tablename__ = "savings"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255), nullable=False, default="")


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    daily_budget = db.Column(db.Integer, nullable=False, default=10_000)


def get_settings() -> Settings:
    settings = db.session.get(Settings, 1)
    if settings is None:
        settings = Settings(id=1, daily_budget=10_000)
        db.session.add(settings)
        db.session.commit()
    return settings


def flash_form_errors(form) -> None:
    for messages in form.errors.values():
        for message in messages:
            flash(message, "error")


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ["FLASK_SECRET"]
    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///main.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    setup_login(app)

    with app.app_context():
        db.create_all()
        get_settings()

    @app.template_filter("rub")
    def rub_filter(value: int) -> str:
        return f"{value:,}".replace(",", " ")

    def render_index(
        *,
        open_panel: str | None = None,
        expense_form: ExpenseForm | None = None,
        saving_form: SavingForm | None = None,
        budget_form: BudgetForm | None = None,
    ):
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

        days = compute_days(expenses, settings.daily_budget)
        days_desc = list(reversed(days))
        today = date.today()
        today_state = next((d for d in days if d.date == today), None)
        total_saved = db.session.scalar(select(func.coalesce(func.sum(Saving.amount), 0))) or 0
        auto_remainder_total = sum(d.eod_remainder for d in days if d.date < today)

        visible_days = [
            d for d in days_desc if d.expenses or d.date == today or d.carry_in or d.carry_out
        ]

        if budget_form is None:
            budget_form = BudgetForm(data={"daily_budget": settings.daily_budget})

        return render_template(
            "index.html",
            settings=settings,
            days=visible_days,
            today=today,
            today_state=today_state,
            savings=savings,
            total_saved=total_saved,
            auto_remainder_total=auto_remainder_total,
            categories=categories,
            expense_form=expense_form or ExpenseForm(),
            saving_form=saving_form or SavingForm(),
            budget_form=budget_form,
            delete_form=DeleteForm(),
            open_panel=open_panel,
        )

    @app.route("/")
    @login_required
    def index():
        return render_index()

    @app.post("/expenses")
    @login_required
    def add_expense():
        form = ExpenseForm()
        if not form.validate_on_submit():
            flash_form_errors(form)
            return render_index(open_panel="expense", expense_form=form), 400

        db.session.add(
            Expense(
                date=form.date.data,
                amount=form.amount.data,
                category=form.category.data.strip(),
                description=(form.description.data or "").strip(),
            )
        )
        db.session.commit()
        flash("Трата добавлена", "success")
        return redirect(url_for("index"))

    @app.post("/expenses/<int:expense_id>/delete")
    @login_required
    def delete_expense(expense_id: int):
        form = DeleteForm()
        if not form.validate_on_submit():
            flash_form_errors(form)
            return redirect(url_for("index"))

        expense = db.session.get(Expense, expense_id)
        if expense is None:
            flash("Трата не найдена", "error")
            return redirect(url_for("index"))
        db.session.delete(expense)
        db.session.commit()
        flash("Трата удалена", "success")
        return redirect(url_for("index"))

    @app.post("/savings")
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
        return redirect(url_for("index"))

    @app.post("/savings/<int:saving_id>/delete")
    @login_required
    def delete_saving(saving_id: int):
        form = DeleteForm()
        if not form.validate_on_submit():
            flash_form_errors(form)
            return redirect(url_for("index"))

        saving = db.session.get(Saving, saving_id)
        if saving is None:
            flash("Сейв не найден", "error")
            return redirect(url_for("index"))
        db.session.delete(saving)
        db.session.commit()
        flash("Сейв удалён", "success")
        return redirect(url_for("index"))

    @app.post("/settings/budget")
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
        return redirect(url_for("index"))

    return app
