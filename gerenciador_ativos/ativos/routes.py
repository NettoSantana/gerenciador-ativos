from flask import Blueprint, render_template, request, redirect, url_for
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo, Cliente
from gerenciador_ativos.ativos.service import criar_ativo, atualizar_ativo, excluir_ativo
from gerenciador_ativos.auth.decorators import login_required, gerente_required

ativos_bp = Blueprint("ativos", __name__, url_prefix="/ativos")


# LISTAGEM
@ativos_bp.route("/")
@login_required
@gerente_required
def lista():
    ativos = Ativo.query.all()
    return render_template("ativos/lista.html", ativos=ativos)


# PAINEL
@ativos_bp.route("/painel/<int:id>")
@login_required
@gerente_required
def painel(id):
    ativo = Ativo.query.get_or_404(id)
    return render_template("ativos/painel.html", ativo=ativo)


# NOVO ATIVO
@ativos_bp.route("/novo", methods=["GET", "POST"])
@login_required
@gerente_required
def novo():
    clientes = Cliente.query.all()

    if request.method == "POST":
        nome = request.form.get("nome")
        categoria = request.form.get("categoria")
        imei = request.form.get("imei")
        cliente_id = int(request.form.get("cliente_id"))
        observacoes = request.form.get("observacoes")

        # 🔥 NOVO CAMPO
        consumo_litros_hora = float(request.form.get("consumo_litros_hora") or 0)

        criar_ativo(
            nome=nome,
            categoria=categoria,
            imei=imei,
            cliente_id=cliente_id,
            observacoes=observacoes,
            consumo_litros_hora=consumo_litros_hora
        )
        return redirect(url_for("ativos.lista"))

    return render_template("ativos/novo.html", clientes=clientes)


# EDITAR ATIVO
@ativos_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
@gerente_required
def editar(id):
    ativo = Ativo.query.get_or_404(id)
    clientes = Cliente.query.all()

    if request.method == "POST":
        nome = request.form.get("nome")
        categoria = request.form.get("categoria")
        imei = request.form.get("imei")
        cliente_id = int(request.form.get("cliente_id"))
        observacoes = request.form.get("observacoes")

        # 🔥 NOVO CAMPO
        consumo_litros_hora = float(request.form.get("consumo_litros_hora") or 0)

        atualizar_ativo(
            ativo=ativo,
            nome=nome,
            categoria=categoria,
            imei=imei,
            cliente_id=cliente_id,
            observacoes=observacoes,
            consumo_litros_hora=consumo_litros_hora
        )
        return redirect(url_for("ativos.lista"))

    return render_template(
        "ativos/editar.html",
        ativo=ativo,
        clientes=clientes
    )


# EXCLUIR
@ativos_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
@gerente_required
def excluir(id):
    ativo = Ativo.query.get_or_404(id)
    excluir_ativo(ativo)
    return redirect(url_for("ativos.lista"))
