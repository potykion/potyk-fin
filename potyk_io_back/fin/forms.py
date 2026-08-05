from datetime import date, timedelta
import os

from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, StringField, SubmitField
from wtforms.validators import AnyOf, DataRequired, InputRequired, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    secret = StringField(
        "Секрет",
        validators=[
            DataRequired(),
            AnyOf([os.environ["FLASK_SECRET"]], message="неверный секрет"),
        ],
        render_kw={
            "required": True,
            "placeholder": "секрет",
            "autocomplete": "current-password",
        },
    )
    submit = SubmitField("Войти")


def _yesterday() -> date:
    return date.today() - timedelta(days=1)


class ExpenseForm(FlaskForm):
    amount = IntegerField(
        "Сумма",
        validators=[InputRequired(), NumberRange(min=1, message="Укажи положительную сумму")],
    )
    date = DateField("Дата", validators=[DataRequired()], default=_yesterday)
    category = StringField(
        "Категория",
        validators=[DataRequired(message="Укажи категорию"), Length(max=64)],
    )
    description = StringField("Описание", validators=[Optional(), Length(max=255)], default="")
    submit = SubmitField("Добавить трату")


class SavingForm(FlaskForm):
    amount = IntegerField(
        "Сумма",
        validators=[InputRequired(), NumberRange(min=1, message="Укажи положительную сумму")],
    )
    date = DateField("Дата", validators=[DataRequired()], default=date.today)
    note = StringField("Заметка", validators=[Optional(), Length(max=255)], default="")
    submit = SubmitField("Зафиксировать")


class BudgetForm(FlaskForm):
    daily_budget = IntegerField(
        "Новый бюджет (₽)",
        validators=[InputRequired(), NumberRange(min=1, message="Укажи положительный бюджет")],
    )
    submit = SubmitField("Сохранить")


class DeleteForm(FlaskForm):
    submit = SubmitField("✕")
