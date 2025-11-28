from flask import render_template, request, redirect, url_for, flash, session
from gerenciador_ativos.auth import auth_bp
from gerenciador_ativos.auth.service import autenticar_usuario


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        usuario = autenticar_usuario(email, senha)
        if not usuario:
            flash("Usuário ou senha inválidos.", "danger")
            return render_template("auth/login.html")

        # guarda dados mínimos na sessão
        session["user_id"] = usuario.id
        session["user_nome"] = usuario.nome
        session["user_tipo"] = usuario.tipo
        session["cliente_id"] = usuario.cliente_id

        flash(f"Bem-vindo(a), {usuario.nome}!", "success")

        # redireciona conforme o tipo
        if usuario.is_interno():
            return redirect(url_for("dashboards.dashboard_gerente"))
        else:
            # tipo cliente → manda para o PORTAL DO CLIENTE NOVO
            return redirect(url_for("portal.dashboard_cliente"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))
