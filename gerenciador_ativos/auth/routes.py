from flask import render_template, request, redirect, url_for, flash, session
from gerenciador_ativos.auth import auth_bp
from gerenciador_ativos.auth.service import autenticar_usuario
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario


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
            # tipo cliente → manda para o PORTAL DO CLIENTE
            return redirect(url_for("portal.dashboard_cliente"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))


# ============================================================
# ROTA INTERNA SEGURA PARA RESETAR SENHA DO ADMIN
# ============================================================

@auth_bp.route("/internal/reset-admin")
def internal_reset_admin():
    """
    Rota interna para redefinir a senha do admin.

    Uso:
      /internal/reset-admin?token=NETTO123RESET

    Somente se o token for EXATAMENTE NETTO123RESET.
    """
    token = request.args.get("token")

    if token != "NETTO123RESET":
        # não revela nada, só nega
        return "Acesso negado.", 403

    admin = Usuario.query.filter_by(email="admin@admin.com").first()

    # se não existir, cria; se existir, reseta a senha
    if not admin:
        admin = Usuario(
            nome="Administrador",
            email="admin@admin.com",
            tipo="admin",
            ativo=True,
        )
        db.session.add(admin)

    admin.set_password("admin123")
    db.session.commit()

    return "Senha do admin redefinida para admin123."
