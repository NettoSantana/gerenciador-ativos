from flask import Blueprint, jsonify
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.ativos.utils import calcular_horas_motor

dashboard_api_bp = Blueprint(
    "dashboard_api",
    __name__,
    url_prefix="/api"
)


@dashboard_api_bp.route("/dashboard-geral", methods=["GET"])
def dashboard_geral_api():
    """
    Dashboard Geral (TV)
    """

    ativos = Ativo.query.filter_by(ativo=True).all()
    dados = []

    for ativo in ativos:
        dados.append({
            "embarcacao": ativo.nome,
            "cotista_dia": "—",
            "horas": calcular_horas_motor(ativo),
            "lavagem_interna": "—",
            "pendencias": "—",
            "bateria": ativo.tensao_bateria or "—"
        })

    return jsonify(dados)
