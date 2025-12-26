from flask import Blueprint, render_template
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.auth.decorators import login_required

painel_bp = Blueprint("painel_ativos", __name__, url_prefix="/ativos")


def calcular_consumo(ativo: Ativo):
    horas_offset = ativo.horas_offset or 0.0
    horas_sistema = ativo.horas_sistema or 0.0
    horas_motor = horas_offset + horas_sistema

    consumo_lph = ativo.consumo_lph or 0.0
    consumo_total = horas_motor * consumo_lph

    return {
        "horas_motor": round(horas_motor, 2),
        "consumo_lph": round(consumo_lph, 2),
        "consumo_total": round(consumo_total, 2),
    }


@painel_bp.route("/<int:id>/painel")
@login_required
def painel(id):
    ativo = Ativo.query.get_or_404(id)
    dados = calcular_consumo(ativo)

    return render_template(
        "ativos/painel.html",
        ativo=ativo,
        **dados,
    )


@painel_bp.route("/<int:id>/consumo")
@login_required
def consumo(id):
    ativo = Ativo.query.get_or_404(id)
    dados = calcular_consumo(ativo)

    return render_template(
        "ativos/consumo.html",
        ativo=ativo,
        **dados,
    )
