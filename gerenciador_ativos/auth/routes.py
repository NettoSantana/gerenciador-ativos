from urllib.parse import urlparse, urljoin

from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user

from gerenciador_ativos.auth import auth_bp
from gerenciador_ativos.auth.service import autenticar_usuario
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario, Cliente


def _is_safe_next_url(target: str) -> bool:
    if not target:
        return False
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and ref.netloc == test.netloc


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
    # se já está logado, manda pra home certa
    if current_user.is_authenticated:
        tipo = session.get("user_tipo")
        if tipo in ["admin", "gerente"]:
            return redirect(url_for("dashboard_geral.dashboard_gerente"))
        return redirect(url_for("portal.dashboard_cliente"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha") or ""

        usuario = autenticar_usuario(email, senha)
        if not usuario:
            flash("Usuário ou senha inválidos.", "danger")
            return render_template("auth/login.html")

        # 🔥 ESSENCIAL: autentica no Flask-Login (senão login_required vira loop)
        login_user(usuario)

        # mantém sessão para templates/menu
        session["user_id"] = usuario.id
        session["user_nome"] = usuario.nome
        session["user_tipo"] = usuario.tipo
        session["cliente_id"] = usuario.cliente_id

        flash(f"Bem-vindo(a), {usuario.nome}!", "success")

        # respeita o next quando for seguro
        next_url = request.args.get("next") or request.form.get("next")
        if next_url and _is_safe_next_url(next_url):
            # cliente não pode cair em rota interna
            if usuario.tipo == "cliente" and next_url.startswith("/dashboard"):
                next_url = None
        else:
            next_url = None

        # home padrão por perfil
        if usuario.is_interno():
            default_url = url_for("dashboard_geral.dashboard_gerente")
        else:
            default_url = url_for("portal.dashboard_cliente")

        return redirect(next_url or default_url)

    return render_template("auth/login.html")


# ============================================================
# LOGOUT
# ============================================================

@auth_bp.route("/logout")
def logout():
    logout_user()
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))


# ============================================================
# CADASTRO LIVRE — com criação automática de CLIENTE
# ============================================================

@auth_bp.route("/register", methods=["POST"])
def register():
    """Cadastro simples para campanhas, com criação automática de cliente."""
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

    # 1 — Criar CLIENTE automático
    cliente = Cliente(
        tipo="PF",
        nome=nome,
        email=email,
        ativo=True
    )
    db.session.add(cliente)
    db.session.flush()

    # 2 — Criar USUÁRIO vinculado
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
