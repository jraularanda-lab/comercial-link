from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from models import Usuario

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = Usuario.query.filter_by(usuario=request.form["usuario"], activo=True).first()
        if u and u.check_password(request.form["password"]):
            login_user(u)
            return redirect(url_for("dashboard.index"))
        flash("Usuario o contraseña incorrectos.", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
