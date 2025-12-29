from flask import Blueprint, render_template
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.auth.decorators import login_required
from gerenciador_ativos.ativos.utils import calcular_horas_motor

painel_bp = Blueprint("painel_ativos", __name__, url_prefix="/ativos")


@painel_bp.route("/<int:id>/painel")
@login_required
def painel(id):
    ativo = Ativo.query.get_or_404(id)

    horas_motor = calcular_horas_motor(ativo)

    return render_template(
        "ativos/painel.html",
        ativo=ativo,
        horas_motor=horas_motor
    )
