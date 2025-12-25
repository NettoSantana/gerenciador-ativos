from flask import render_template, request, redirect, url_for, flash, session
from gerenciador_ativos.auth.decorators import login_required
from gerenciador_ativos.auth.service import autenticar_usuario
from gerenciador_ativos.extensions import db

from gerenciador_ativos.models.usuario import Usuario
from gerenciador_ativos.models.clientes import Cliente
from gerenciador_ativos.auth import auth_bp


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        usuario = autenticar_usuario(email, senha)

        if not usuario:
            flash("Credenciais inválidas.", "danger")
            return redirect(url_for("auth.login"))

        session["user_id"] = usuario.id
        session["user_tipo"] = usuario.tipo

        return redirect(url_for("dashboards.index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
