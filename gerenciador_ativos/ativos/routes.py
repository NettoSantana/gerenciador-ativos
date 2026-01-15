from flask import Blueprint, render_template, request, redirect, url_for
from gerenciador_ativos.models import Ativo, Cliente
from gerenciador_ativos.ativos.service import criar_ativo, atualizar_ativo, excluir_ativo
from gerenciador_ativos.ativos.utils import calcular_horas_motor
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

    # 🔥 fonte única da verdade
    horas_motor = calcular_horas_motor(ativo)

    return render_template(
        "ativos/painel.html",
        ativo=ativo,
        horas_motor=horas_motor
    )


# NOVO ATIVO
@ativos_bp.route("/novo", methods=["GET", "POST"])
@login_required
@gerente_required
def novo():
    clientes = Cliente.query.all()

    if request.method == "POST":
        nome = request.form.get("nome")
        categoria = request.form.get("categoria")

        # Identificadores de rastreamento (novo)
        tracking_provider = request.form.get("tracking_provider") or "mobiltracker"
        tracker_id = request.form.get("tracker_id")
        imei = request.form.get("imei")

        # Cliente
        cliente_id_raw = request.form.get("cliente_id")
        cliente_id = int(cliente_id_raw) if cliente_id_raw else None

        observacoes = request.form.get("observacoes")

        criar_ativo(
            nome=nome,
            categoria=categoria,
            cliente_id=cliente_id,
            imei=imei,
            tracker_id=tracker_id,
            tracking_provider=tracking_provider,
            observacoes=observacoes,
        )
        return redirect(url_for("ativos.lista"))

    return render_template("ativos/novo.html", clientes=clientes)


# EDITAR
@ativos_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
@gerente_required
def editar(id):
    ativo = Ativo.query.get_or_404(id)
    clientes = Cliente.query.all()

    if request.method == "POST":
        nome = request.form.get("nome")
        categoria = request.form.get("categoria")

        # Identificadores de rastreamento (novo)
        tracking_provider = request.form.get("tracking_provider") or "mobiltracker"
        tracker_id = request.form.get("tracker_id")
        imei = request.form.get("imei")

        # Cliente
        cliente_id_raw = request.form.get("cliente_id")
        cliente_id = int(cliente_id_raw) if cliente_id_raw else None

        observacoes = request.form.get("observacoes")

        atualizar_ativo(
            ativo=ativo,
            nome=nome,
            categoria=categoria,
            cliente_id=cliente_id,
            imei=imei,
            tracker_id=tracker_id,
            tracking_provider=tracking_provider,
            observacoes=observacoes,
        )
        return redirect(url_for("ativos.lista"))

    return render_template("ativos/editar.html", ativo=ativo, clientes=clientes)


# EXCLUIR
@ativos_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
@gerente_required
def excluir(id):
    ativo = Ativo.query.get_or_404(id)
    excluir_ativo(ativo)
    return redirect(url_for("ativos.lista"))
