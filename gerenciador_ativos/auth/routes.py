from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user

from gerenciador_ativos.auth import auth_bp
from gerenciador_ativos.auth.service import autenticar_usuario
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario, Cliente


def _safe_next_url() -> str | None:
    nxt = request.args.get("next") or request.form.get("next")
    if nxt and isinstance(nxt, str) and nxt.startswith("/"):
        return nxt
    return None


# ============================================================
# ROTA RAIZ → sempre envia para /login
# ============================================================

@auth_bp.route("/")
def index_redirect():
    return redirect(url_for("auth.login"))


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha") or ""

        usuario = autenticar_usuario(email, senha)
        if not usuario:
            flash("Usuário ou senha inválidos.", "danger")
            return render_template("auth/login.html", next=_safe_next_url())

        # 🔐 LOGIN REAL NO FLASK-LOGIN
        login_user(usuario)

        # dados extras na sessão (OK manter)
        session["user_id"] = usuario.id
        session["user_nome"] = usuario.nome
        session["user_tipo"] = usuario.tipo
        session["cliente_id"] = usuario.cliente_id

        flash(f"Bem-vindo(a), {usuario.nome}!", "success")

        nxt = _safe_next_url()
        if nxt:
            return redirect(nxt)

        if usuario.is_interno():
            return redirect(url_for("dashboard_geral.dashboard_gerente"))

        return redirect(url_for("portal.dashboard_cliente"))

    return render_template("auth/login.html", next=_safe_next_url())


# ============================================================
# LOGOUT
# ============================================================

@auth_bp.route("/logout")
def logout():
    logout_user()          # 🔐 limpa Flask-Login
    session.clear()        # limpa seus dados extras
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))


# ============================================================
# CADASTRO LIVRE — com criação automática de CLIENTE
# ============================================================

@auth_bp.route("/register", methods=["POST"])
def register():
    nome = (request.form.get("nome") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    senha = request.form.get("senha") or ""
    confirmar = request.form.get("confirmar") or ""

    if not nome or not email or not senha:
        flash("Preencha todos os campos.", "danger")
        return redirect(url_for("auth.login"))

    if senha != confirmar:
        flash("As senhas não coincidem.", "danger")
        return redirect(url_for("auth.login"))

    if Usuario.query.filter_by(email=email).first():
        flash("Este e-mail já está cadastrado.", "warning")
        return redirect(url_for("auth.login"))

    cliente = Cliente(
        tipo="PF",
        nome=nome,
        email=email,
        ativo=True
    )
    db.session.add(cliente)
    db.session.flush()

    usuario = Usuario(
        nome=nome,
        email=email,
        tipo="cliente",
        ativo=True,
        cliente_id=cliente.id
    )
    usuario.set_password(senha)

    db.session.add(usuario)
    db.session.commit()

    flash("Conta criada com sucesso! Faça login para continuar.", "success")
    return redirect(url_for("auth.login"))


# ============================================================
# RESET DE SENHA DO ADMIN
# ============================================================

@auth_bp.route("/internal/reset-admin")
def internal_reset_admin():
    token = request.args.get("token")

    if token != "NETTO123RESET":
        return "Acesso negado.", 403

    admin = Usuario.query.filter_by(email="admin@admin.com").first()

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
