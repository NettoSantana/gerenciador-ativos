from flask import Blueprint, jsonify

dashboard_api_bp = Blueprint(
    "dashboard_api",
    __name__,
    url_prefix="/api"
)


@dashboard_api_bp.route("/dashboard-geral", methods=["GET"])
def dashboard_geral_api():
    """
    Endpoint dedicado para o Dashboard Geral (TV).
    Retorna JSON pronto para consumo visual.
    (dados mockados neste primeiro passo)
    """

    dados = [
        {
            "embarcacao": "—",
            "cotista_dia": "—",
            "horas": "—",
            "lavagem_interna": "—",
            "pendencias": "—",
            "bateria": "—"
        }
    ]

    return jsonify(dados)
