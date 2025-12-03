from flask import render_template, request, redirect, url_for, flash, session
from gerenciador_ativos.auth.decorators import login_required, role_required
from gerenciador_ativos.usuarios import usuarios_bp
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario


# ============================================================
# CONFIGURAÇÃO DO ADMIN PRINCIPAL
# ============================================================
ADMIN_PRINCIPAL_EMAIL = "admin@admin.com"


# ============================================================
# LISTA DE USUÁRIOS
# ============================================================

@usuarios_bp.route("/")
@login_required
@role_required(["admin", "gerente"])
def lista():
    usuarios = Usuario.query.order_by(Usuario.nome.asc()).all()
    return render_template("usuarios/lista.html", usuarios=usuarios)


# ============================================================
# NOVO USUÁRIO
# ============================================================

@usuarios_bp.route("/novo", methods=["GET", "POST"])
@login_required
@role_required(["admin", "gerente"])
def novo():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        tipo = request.form.get("tipo")

        if Usuario.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "warning")
            return redirect(url_for("usuarios.lista"))

        usuario = Usuario(
            nome=nome,
            email=email,
            tipo=tipo,
            ativo=True
        )
        usuario.set_password(senha)

        db.session.add(usuario)
        db.session.commit()

        flash("Usuário criado com sucesso.", "success")
        return redirect(url_for("usuarios.lista"))

    return render_template("usuarios/novo.html")


# ============================================================
# EDITAR USUÁRIO
# ============================================================

@usuarios_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
@role_required(["admin", "gerente"])
def editar(id):
    usuario = Usuario.query.get_or_404(id)

    if request.method == "POST":
        usuario.nome = request.form.get("nome")
        usuario.email = request.form.get("email")
        usuario.tipo = request.form.get("tipo")

        db.session.commit()
        flash("Usuário atualizado com sucesso.", "success")
        return redirect(url_for("usuarios.lista"))

    return render_template("usuarios/editar.html", usuario=usuario)


# ============================================================
# ATIVAR / DESATIVAR
# ============================================================

@usuarios_bp.route("/toggle/<int:id>")
@login_required
@role_required(["admin", "gerente"])
def toggle(id):
    usuario = Usuario.query.get_or_404(id)

    usuario.ativo = not usuario.ativo
    db.session.commit()

    flash("Status atualizado.", "info")
    return redirect(url_for("usuarios.lista"))


# ============================================================
# EXCLUSÃO REAL
# ============================================================

@usuarios_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
@role_required(["admin", "gerente"])
def excluir(id):
    usuario = Usuario.query.get_or_404(id)

    usuario_logado_tipo = session.get("user_tipo")
    usuario_logado_id = session.get("user_id")

    # 1 — ninguém pode excluir o admin principal
    if usuario.email == ADMIN_PRINCIPAL_EMAIL:
        flash("O administrador principal não pode ser excluído.", "danger")
        return redirect(url_for("usuarios.lista"))

    # 2 — ninguém pode excluir a si mesmo
    if usuario.id == usuario_logado_id:
        flash("Você não pode excluir seu próprio usuário.", "danger")
        return redirect(url_for("usuarios.lista"))

    # 3 — gerente NÃO exclui gerente
    if usuario_logado_tipo == "gerente" and usuario.tipo == "gerente":
        flash("Gerentes não podem excluir outros gerentes.", "danger")
        return redirect(url_for("usuarios.lista"))

    # 4 — admin pode excluir qualquer um (menos admin principal)
    # (nenhum bloco adicional necessário)

    db.session.delete(usuario)
    db.session.commit()

    flash("Usuário excluído permanentemente.", "danger")
    return redirect(url_for("usuarios.lista"))
