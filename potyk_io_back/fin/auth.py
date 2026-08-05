from flask import flash, redirect, render_template, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user

from potyk_io_back.fin.forms import LoginForm


class SecretUser(UserMixin):
    def __init__(self, secret: str):
        self.secret = secret

    def get_id(self) -> str:
        return self.secret


def setup_login(app, bp):
    login_manager = LoginManager()

    @login_manager.user_loader
    def load_user(secret):
        return SecretUser(secret)

    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect(url_for("fin.login"))

    @bp.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if form.is_submitted():
            if form.validate():
                login_user(SecretUser(form.secret.data))
                return redirect(url_for("fin.index"))
            flash("неверный секрет", "error")
        return render_template("potyk-fin/login.html", form=form)

    @bp.get("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("fin.login"))

    login_manager.init_app(app)
