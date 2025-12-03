from flask import render_template, request, redirect, url_for, flash, session
from gerenciador_ativos.auth import auth_bp
from gerenciador_ativos.auth.service import autenticar_usuario
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario, Cliente


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        usuario = autenticar_usuario(email, senha)
        if not usuario:
            flash("Usuário ou senha inválidos.", "danger")
            return render_template("auth/login.html")

        # guarda dados na sessão
        session["user_id"] = usuario.id
        session["user_nome"] = usuario.nome
        session["user_tipo"] = usuario.tipo
        session["cliente_id"] = usuario.cliente_id

        flash(f"Bem-vindo(a), {usuario.nome}!", "success")

        # rota conforme o tipo
        if usuario.is_interno():
            return redirect(url_for("dashboards.dashboard_gerente"))
        else:
            return redirect(url_for("portal.dashboard_cliente"))

    return render_template("auth/login.html")


# ============================================================
# LOGOUT
# ============================================================

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))


# ============================================================
# CADASTRO LIVRE — com criação automática de CLIENTE
# ============================================================

@auth_bp.route("/register", methods=["POST"])
def register():
    """Cadastro simples para campanhas, com criação automática de cliente."""
    
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha")
    confirmar = request.form.get("confirmar")

    # validações básicas
    if not nome or not email or not senha:
        flash("Preencha todos os campos.", "danger")
        return redirect(url_for("auth.login"))

    if senha != confirmar:
        flash("As senhas não coincidem.", "danger")
        return redirect(url_for("auth.login"))

    # email duplicado
    if Usuario.query.filter_by(email=email).first():
        flash("Este e-mail já está cadastrado.", "warning")
        return redirect(url_for("auth.login"))

    # ===========================
    # 1 — Criar CLIENTE automático
    # ===========================
    cliente = Cliente(
        tipo="PF",
        nome=nome,
        email=email,
        ativo=True
    )
    db.session.add(cliente)
    db.session.flush()  # garante ID imediato

    # ===========================
    # 2 — Criar USUÁRIO vinculado
    # ===========================
    usuario = Usuario(
        nome=nome,
        email=email,
        tipo="cliente",   # padrão para campanhas
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
