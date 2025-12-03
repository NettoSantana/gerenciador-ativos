from flask import render_template, request, redirect, url_for, flash
from gerenciador_ativos.clientes import clientes_bp
from gerenciador_ativos.models import Cliente, Ativo
from gerenciador_ativos.auth.decorators import login_required, role_required
from gerenciador_ativos.clientes.service import (
    criar_cliente, atualizar_cliente,
    desativar_cliente, ativar_cliente
)


# ============================================================
# LISTA
# ============================================================

@clientes_bp.route("/")
@login_required
@role_required(["admin", "gerente"])
def lista():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template("clientes/lista.html", clientes=clientes)


# ============================================================
# NOVO CLIENTE
# ============================================================

@clientes_bp.route("/novo", methods=["GET", "POST"])
@login_required
@role_required(["admin", "gerente"])
def novo():
    if request.method == "POST":
        tipo = request.form.get("tipo")
        nome = request.form.get("nome")
        cpf_cnpj = request.form.get("cpf_cnpj")
        telefone = request.form.get("telefone")
        email = request.form.get("email")
        endereco = request.form.get("endereco")
        observacoes = request.form.get("observacoes")

        criar_cliente(tipo, nome, cpf_cnpj, telefone, email, endereco, observacoes)
        flash("Cliente criado com sucesso!", "success")
        return redirect(url_for("clientes.lista"))

    return render_template("clientes/novo.html")


# ============================================================
# EDITAR CLIENTE
# ============================================================

@clientes_bp.route("/editar/<int:id>", methods=["GET","POST"])
@login_required
@role_required(["admin", "gerente"])
def editar(id):
    cliente = Cliente.query.get_or_404(id)

    if request.method == "POST":
        tipo = request.form.get("tipo")
        nome = request.form.get("nome")
        cpf_cnpj = request.form.get("cpf_cnpj")
        telefone = request.form.get("telefone")
        email = request.form.get("email")
        endereco = request.form.get("endereco")
        observacoes = request.form.get("observacoes")

        atualizar_cliente(cliente, tipo, nome, cpf_cnpj, telefone, email, endereco, observacoes)
        flash("Cliente atualizado!", "success")
        return redirect(url_for("clientes.lista"))

    return render_template("clientes/editar.html", cliente=cliente)


# ============================================================
# ATIVAR / DESATIVAR
# ============================================================

@clientes_bp.route("/desativar/<int:id>")
@login_required
@role_required(["admin", "gerente"])
def desativar(id):
    cliente = Cliente.query.get_or_404(id)
    desativar_cliente(cliente)
    flash("Cliente desativado.", "warning")
    return redirect(url_for("clientes.lista"))


@clientes_bp.route("/ativar/<int:id>")
@login_required
@role_required(["admin", "gerente"])
def ativar(id):
    cliente = Cliente.query.get_or_404(id)
    ativar_cliente(cliente)
    flash("Cliente ativado!", "success")
    return redirect(url_for("clientes.lista"))


# ============================================================
# EXCLUSÃO REAL (APAGA DO BANCO)
# ============================================================

@clientes_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
@role_required(["admin", "gerente"])
def excluir(id):
    cliente = Cliente.query.get_or_404(id)

    # (Opcional) Impedir excluir cliente com ativos vinculados
    ativos = Ativo.query.filter_by(cliente_id=id).all()
    if ativos:
        flash("Este cliente possui ativos cadastrados. Remova ou transfira antes de excluir.", "danger")
        return redirect(url_for("clientes.lista"))

    # Exclusão definitiva
    from gerenciador_ativos.extensions import db
    db.session.delete(cliente)
    db.session.commit()

    flash("Cliente excluído permanentemente.", "danger")
    return redirect(url_for("clientes.lista"))
