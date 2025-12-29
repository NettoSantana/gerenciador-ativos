from flask import Blueprint, render_template
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.auth.decorators import login_required
from gerenciador_ativos.ativos.utils import calcular_consumo_total

painel_bp = Blueprint("painel_ativos", __name__, url_prefix="/ativos")


@painel_bp.route("/<int:id>/painel")
@login_required
def painel(id):
    ativo = Ativo.query.get_or_404(id)
    dados = calcular_consumo_total(ativo)

    return render_template(
        "ativos/painel.html",
        ativo=ativo,
        **dados,
    )


@painel_bp.route("/<int:id>/consumo")
@login_required
def consumo(id):
    ativo = Ativo.query.get_or_404(id)
    dados = calcular_consumo_total(ativo)

    return render_template(
        "ativos/consumo.html",
        ativo=ativo,
        **dados,
    )
