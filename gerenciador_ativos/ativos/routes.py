from flask import Blueprint, render_template, request, redirect, url_for, flash
from gerenciador_ativos.auth.decorators import login_required
from gerenciador_ativos.models import Ativo, Cliente
from gerenciador_ativos.ativos.service import criar_ativo, atualizar_ativo, deletar_ativo

# CORREÇÃO → acrescentado "__name__"
ativos_bp = Blueprint("ativos", __name__, url_prefix="/ativos")


@ativos_bp.route("/")
@login_required
def lista():
    ativos = Ativo.query.all()
    return render_template("ativos/lista.html", ativos=ativos)


@ativos_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    clientes = Cliente.query.order_by(Cliente.nome).all()

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id")
        nome = request.form.get("nome")
        categoria = request.form.get("categoria")
        imei = request.form.get("imei")
        observacoes = request.form.get("observacoes")

        criar_ativo(
            cliente_id=int(cliente_id),
            nome=nome,
            categoria=categoria,
            imei=imei,
            observacoes=observacoes
        )

        flash("Ativo criado com sucesso!", "success")
        return redirect(url_for("ativos.lista"))

    return render_template("ativos/novo.html", clientes=clientes)


@ativos_bp.route("/<int:ativo_id>/editar", methods=["GET", "POST"])
@login_required
def editar(ativo_id):
    ativo = Ativo.query.get_or_404(ativo_id)
    clientes = Cliente.query.order_by(Cliente.nome).all()

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id")
        nome = request.form.get("nome")
        categoria = request.form.get("categoria")
        imei = request.form.get("imei")
        observacoes = request.form.get("observacoes")

        atualizar_ativo(
            ativo_id,
            cliente_id=int(cliente_id),
            nome=nome,
            categoria=categoria,
            imei=imei,
            observacoes=observacoes
        )

        flash("Ativo atualizado com sucesso!", "success")
        return redirect(url_for("ativos.lista"))

    return render_template("ativos/editar.html", ativo=ativo, clientes=clientes)


@ativos_bp.route("/<int:ativo_id>/delete", methods=["POST"])
@login_required
def remover(ativo_id):
    deletar_ativo(ativo_id)
    flash("Ativo removido com sucesso!", "success")
    return redirect(url_for("ativos.lista"))
