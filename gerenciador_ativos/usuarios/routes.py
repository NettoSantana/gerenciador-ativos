from flask import render_template, request, redirect, url_for, flash, session
from gerenciador_ativos.auth.decorators import login_required, role_required
from gerenciador_ativos.usuarios import usuarios_bp
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario, Cliente


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
# NOVO USUÁRIO (CRIANDO CLIENTE AUTOMÁTICO)
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

        telefone = request.form.get("telefone")
        cpf_cnpj = request.form.get("cpf_cnpj")
        endereco = request.form.get("endereco")
        observacoes = request.form.get("observacoes")

        # Verifica duplicidade
        if Usuario.query.filter_by(email=email).first():
            flash("Já existe um usuário com este e-mail.", "danger")
            return redirect(url_for("usuarios.novo"))

        # Criação do usuário
        usuario = Usuario(
            nome=nome,
            email=email,
            tipo=tipo,
            ativo=True
        )
        usuario.set_password(senha)

        db.session.add(usuario)
        db.session.flush()  # permite pegar o ID sem commit

        # Se for usuário CLIENTE → cria automaticamente CLIENTE
        if tipo == "cliente":
            cliente = Cliente(
                tipo="",                  # tipo vazio porque você escolheu a opção 4
                nome=nome,
                email=email,
                telefone=telefone,
                cpf_cnpj=cpf_cnpj,
                endereco=endereco,
                observacoes=observacoes,
                ativo=True
            )
            db.session.add(cliente)
            db.session.flush()
            usuario.cliente_id = cliente.id

        db.session.commit()

        flash("Usuário criado com sucesso!", "success")
        return redirect(url_for("usuarios.lista"))

    return render_template("usuarios/novo.html")


# ============================================================
# EDITAR USUÁRIO (SINCRONIZAÇÃO COM CLIENTE)
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

        # SINCRONIZA usuário → cliente
        if usuario.cliente_id:
            cliente = Cliente.query.get(usuario.cliente_id)
            if cliente:
                cliente.nome = usuario.nome
                cliente.email = usuario.email

        db.session.commit()

        flash("Usuário atualizado com sucesso!", "success")
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

    # não permite excluir admin principal
    if usuario.email == "admin@admin.com":
        flash("O administrador principal não pode ser excluído.", "danger")
        return redirect(url_for("usuarios.lista"))

    # não permite excluir a si mesmo
    if usuario.id == session.get("user_id"):
        flash("Você não pode excluir seu próprio usuário.", "danger")
        return redirect(url_for("usuarios.lista"))

    # gerente não exclui gerente
    if session.get("user_tipo") == "gerente" and usuario.tipo == "gerente":
        flash("Gerentes não podem excluir outros gerentes.", "danger")
        return redirect(url_for("usuarios.lista"))

    # Remove usuário (não remove cliente!)
    db.session.delete(usuario)
    db.session.commit()

    flash("Usuário excluído permanentemente.", "danger")
    return redirect(url_for("usuarios.lista"))
