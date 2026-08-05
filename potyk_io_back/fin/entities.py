from potyk_io_back.core.db import db


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
