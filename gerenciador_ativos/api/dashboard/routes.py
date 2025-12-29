from flask import Blueprint, jsonify
from gerenciador_ativos.models import Ativo

dashboard_api_bp = Blueprint(
    "dashboard_api",
    __name__,
    url_prefix="/api"
)


@dashboard_api_bp.route("/dashboard-geral", methods=["GET"])
def dashboard_geral_api():
    """
    Endpoint dedicado para o Dashboard Geral (TV).

    Dados reais neste passo:
    - Embarcação: Ativo.nome
    - Horas: campo existente no model (ou placeholder)
    - Bateria: tensão da bateria no ativo (ou placeholder)

    Demais campos permanecem como placeholder.
    """

    ativos = Ativo.query.filter_by(ativo=True).all()

    dados = []

    for ativo in ativos:
        dados.append({
            "embarcacao": ativo.nome,
            "cotista_dia": "—",
            "horas": getattr(ativo, "horas_uso", "—"),
            "lavagem_interna": "—",
            "pendencias": "—",
            "bateria": getattr(ativo, "tensao_bateria", "—")
        })

    return jsonify(dados)
