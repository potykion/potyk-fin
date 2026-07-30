import os
from datetime import date

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, select

from budget import compute_days

load_dotenv()

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


def parse_amount(raw: str) -> int | None:
    raw = (raw or "").strip().replace(" ", "").replace(",", "")
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    if value <= 0:
        return None
    return value


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ["FLASK_SECRET"]
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///main.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        get_settings()

    @app.template_filter("rub")
    def rub_filter(value: int) -> str:
        return f"{value:,}".replace(",", " ")

    @app.route("/")
    def index():
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
        )

    @app.post("/expenses")
    def add_expense():
        amount = parse_amount(request.form.get("amount", ""))
        category = (request.form.get("category") or "").strip()
        description = (request.form.get("description") or "").strip()
        expense_date = parse_date(request.form.get("date", "")) or date.today()

        if amount is None:
            flash("Укажи положительную сумму", "error")
            return redirect(url_for("index"))
        if not category:
            flash("Укажи категорию", "error")
            return redirect(url_for("index"))

        db.session.add(
            Expense(
                date=expense_date,
                amount=amount,
                category=category,
                description=description,
            )
        )
        db.session.commit()
        flash("Трата добавлена", "success")
        return redirect(url_for("index"))

    @app.post("/expenses/<int:expense_id>/delete")
    def delete_expense(expense_id: int):
        expense = db.session.get(Expense, expense_id)
        if expense is None:
            flash("Трата не найдена", "error")
            return redirect(url_for("index"))
        db.session.delete(expense)
        db.session.commit()
        flash("Трата удалена", "success")
        return redirect(url_for("index"))

    @app.post("/savings")
    def add_saving():
        amount = parse_amount(request.form.get("amount", ""))
        note = (request.form.get("note") or "").strip()
        saving_date = parse_date(request.form.get("date", "")) or date.today()

        if amount is None:
            flash("Укажи положительную сумму", "error")
            return redirect(url_for("index"))

        db.session.add(Saving(date=saving_date, amount=amount, note=note))
        db.session.commit()
        flash("Сейв зафиксирован", "success")
        return redirect(url_for("index"))

    @app.post("/savings/<int:saving_id>/delete")
    def delete_saving(saving_id: int):
        saving = db.session.get(Saving, saving_id)
        if saving is None:
            flash("Сейв не найден", "error")
            return redirect(url_for("index"))
        db.session.delete(saving)
        db.session.commit()
        flash("Сейв удалён", "success")
        return redirect(url_for("index"))

    @app.post("/settings/budget")
    def update_budget():
        amount = parse_amount(request.form.get("daily_budget", ""))
        if amount is None:
            flash("Укажи положительный бюджет", "error")
            return redirect(url_for("index"))

        settings = get_settings()
        settings.daily_budget = amount
        db.session.commit()
        flash("Бюджет на день обновлён", "success")
        return redirect(url_for("index"))

    return app
