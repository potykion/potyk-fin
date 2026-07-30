import os
import sqlite3

import flask
from flask import Flask, request, g


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ["FLASK_SECRET"]

    DATABASE = "main.db"

    def get_db():
        db = getattr(g, "_database", None)
        if db is None:
            db = g._database = sqlite3.connect(DATABASE)
            db.row_factory = sqlite3.Row
        return db

    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, "_database", None)
        if db is not None:
            db.close()

    @app.route("/")
    def index():
        cur = get_db().cursor()
        rows = cur.execute("SELECT * FROM table").fetchall()
        return flask.render_template("index.html")

    @app.route("/form", methods=["GET", "POST"])
    def form():
        if request.method == "GET":
            return flask.render_template("form.html")
        elif request.method == "POST":
            form = request.form

            cur = get_db().cursor()
            cur.execute(
                """insert into table (col1, col2)
                   values (?, ?)""",
                (form["col1"], form["col2"]),
            )
            cur.connection.commit()

            flask.flash(f"Successfully added", "success")
            return flask.render_template("form.html")

    return app
