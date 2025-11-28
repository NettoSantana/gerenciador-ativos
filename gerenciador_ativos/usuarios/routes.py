from flask import render_template, request, redirect, url_for, flash
from gerenciador_ativos.usuarios import usuarios_bp
from gerenciador_ativos.auth.decorators import login_required, role_required
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario, Cliente
from gerenciador_ativos.usuarios.service import (
    criar_usuario, atualizar_usuario, desativar_usuario, ativar_usuario
)


@usuarios_bp.route("/")
@login_required
@role_required(["admin", "gerente"])
def lista():
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return render_template("usuarios/lista.html", usuarios=usuarios)


@usuarios_bp.route("/novo", methods=["GET", "POST"])
@login_required
@role_required(["admin", "gerente"])
def novo():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        tipo = request.form.get("tipo")
        cliente_id = request.form.get("cliente_id") or None

        # Normaliza e-mail
        if email:
            email = email.lower()

        # Valida e-mail duplicado
        if Usuario.query.filter_by(email=email).first():
            flash("Já existe um usuário com este e-mail.", "danger")
            return redirect(url_for("usuarios.novo"))

        # Se for usuário do tipo cliente, cliente_id é obrigatório
        if tipo == "cliente" and not cliente_id:
            flash("Para usuários do tipo Cliente, é obrigatório selecionar um Cliente.", "danger")
            return redirect(url_for("usuarios.novo"))

        # Converte cliente_id para int ou None
        if cliente_id:
            try:
                cliente_id = int(cliente_id)
            except ValueError:
                cliente_id = None

        criar_usuario(nome, email, senha, tipo, cliente_id)
        flash("Usuário criado com sucesso!", "success")
        return redirect(url_for("usuarios.lista"))

    # GET: carrega lista de clientes para o select
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template("usuarios/novo.html", clientes=clientes)


@usuarios_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
@role_required(["admin", "gerente"])
def editar(id):
    usuario = Usuario.query.get_or_404(id)

    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        tipo = request.form.get("tipo")
        cliente_id = request.form.get("cliente_id") or None

        if email:
            email = email.lower()

        # Se tipo NÃO for cliente, força desligar de qualquer cliente
        if tipo != "cliente":
            cliente_id = None
        else:
            # Tipo cliente: cliente_id é obrigatório
            if not cliente_id:
                flash("Para usuários do tipo Cliente, é obrigatório selecionar um Cliente.", "danger")
                return redirect(url_for("usuarios.editar", id=usuario.id))

            try:
                cliente_id = int(cliente_id)
            except ValueError:
                cliente_id = None
                flash("Cliente selecionado inválido.", "danger")
                return redirect(url_for("usuarios.editar", id=usuario.id))

        atualizar_usuario(usuario, nome, email, tipo, cliente_id)
        flash("Usuário atualizado!", "success")
        return redirect(url_for("usuarios.lista"))

    # GET: carrega lista de clientes para o select
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template("usuarios/editar.html", usuario=usuario, clientes=clientes)


@usuarios_bp.route("/desativar/<int:id>")
@login_required
@role_required(["admin", "gerente"])
def desativar(id):
    usuario = Usuario.query.get_or_404(id)
    desativar_usuario(usuario)
    flash("Usuário desativado.", "warning")
    return redirect(url_for("usuarios.lista"))


@usuarios_bp.route("/ativar/<int:id>")
@login_required
@role_required(["admin", "gerente"])
def ativar(id):
    usuario = Usuario.query.get_or_404(id)
    ativar_usuario(usuario)
    flash("Usuário reativado.", "success")
    return redirect(url_for("usuarios.lista"))
