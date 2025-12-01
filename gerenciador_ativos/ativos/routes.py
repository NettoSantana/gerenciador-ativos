from flask import Blueprint, render_template, request, redirect, url_for
from gerenciador_ativos.extensions import db
from gerenciador_ativos.auth.decorators import login_required
from gerenciador_ativos.ativos.service import criar_ativo, atualizar_ativo, excluir_ativo
from gerenciador_ativos.models import Ativo, Cliente

ativos_bp = Blueprint("ativos", __name__, url_prefix="/ativos")


# ----------------------------------------
# LISTA
# ----------------------------------------
@ativos_bp.route("/")
@login_required
def lista():
    ativos = Ativo.query.all()
    return render_template("ativos/lista.html", ativos=ativos)


# ----------------------------------------
# NOVO
# ----------------------------------------
@ativos_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    clientes = Cliente.query.all()

    if request.method == "POST":
        nome = request.form.get("nome")
        categoria = request.form.get("categoria")
        imei = request.form.get("imei")
        cliente_id = int(request.form.get("cliente_id"))

        criar_ativo(
            nome=nome,
            categoria=categoria,
            imei=imei,
            cliente_id=cliente_id
        )

        return redirect(url_for("ativos.lista"))

    return render_template("ativos/novo.html", clientes=clientes)


# ----------------------------------------
# DETALHE  (NOVO — ESSA ROTA FALTAVA)
# ----------------------------------------
@ativos_bp.route("/<int:id>")
@login_required
def detalhe(id):
    ativo = Ativo.query.get_or_404(id)
    return render_template("ativos/detalhe.html", ativo=ativo)


# ----------------------------------------
# EDITAR
# ----------------------------------------
@ativos_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar(id):
    ativo = Ativo.query.get_or_404(id)
    clientes = Cliente.query.all()

    if request.method == "POST":
        nome = request.form.get("nome")
        categoria = request.form.get("categoria")
        imei = request.form.get("imei")
        cliente_id = int(request.form.get("cliente_id"))

        atualizar_ativo(
            ativo,
            nome=nome,
            categoria=categoria,
            imei=imei,
            cliente_id=cliente_id
        )

        return redirect(url_for("ativos.lista"))

    return render_template("ativos/editar.html", ativo=ativo, clientes=clientes)


# ----------------------------------------
# EXCLUIR
# ----------------------------------------
@ativos_bp.route("/<int:id>/excluir", methods=["POST"])
@login_required
def excluir(id):
    ativo = Ativo.query.get_or_404(id)
    excluir_ativo(ativo)
    return redirect(url_for("ativos.lista"))
