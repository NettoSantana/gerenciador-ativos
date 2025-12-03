from flask import render_template, request, redirect, url_for, flash, session
from gerenciador_ativos.auth.decorators import login_required, role_required
from gerenciador_ativos.usuarios import usuarios_bp
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario


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

    # Impede excluir a si mesmo
    if usuario.id == session.get("user_id"):
        flash("Você não pode excluir seu próprio usuário.", "danger")
        return redirect(url_for("usuarios.lista"))

    db.session.delete(usuario)
    db.session.commit()

    flash("Usuário excluído permanentemente.", "danger")
    return redirect(url_for("usuarios.lista"))
