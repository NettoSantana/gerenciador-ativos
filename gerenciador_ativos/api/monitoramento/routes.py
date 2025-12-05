"""
Rotas de monitoramento: entrega dados de telemetria para o painel.

Integração 100% alinhada com brasilsat.py
"""

from flask import Blueprint, jsonify
from gerenciador_ativos.api.monitoramento.brasilsat import (
    get_telemetria_por_imei,
    BrasilSatError,
)
from gerenciador_ativos.models import Ativo

monitoramento_bp = Blueprint("monitoramento_bp", __name__, url_prefix="/api/monitoramento")


# ------------------------------------------------------------
# FUNÇÃO: transformar telemetria crua em JSON para o painel
# ------------------------------------------------------------

def montar_resposta_painel(telem):
    """
    telem = retorno direto de get_telemetria_por_imei()
    """

    # Agora todas as chaves estão corretas:
    # "motor_ligado", "horas_motor", "tensao_bateria",
    # "latitude", "longitude", "velocidade", "direcao", "servertime"

    return {
        "imei": telem.get("imei"),

        # MOTOR
        "motor_ligado": telem.get("motor_ligado") or False,

        # HORAS
        "horas_motor": round(telem.get("horas_motor") or 0, 2),

        # TENSÃO
        "tensao_bateria": telem.get("tensao_bateria"),

        # LOCALIZAÇÃO
        "latitude": telem.get("latitude"),
        "longitude": telem.get("longitude"),
        "velocidade": telem.get("velocidade"),
        "direcao": telem.get("direcao"),

        # TEMPO
        "servertime": telem.get("servertime"),

        # DEBUG opcional
        # "raw": telem,
    }


# ------------------------------------------------------------
# ROTA: pegar dados de um ativo por IMEI
# ------------------------------------------------------------

@monitoramento_bp.route("/<int:ativo_id>/dados", methods=["GET"])
def obter_dados(ativo_id):
    ativo = Ativo.query.filter_by(id=ativo_id, ativo=True).first()

    if not ativo:
        return jsonify({"error": "Ativo não encontrado."}), 404

    if not ativo.imei:
        return jsonify({"error": "Ativo não possui IMEI cadastrado."}), 400

    try:
        telem = get_telemetria_por_imei(ativo.imei)
    except BrasilSatError as exc:
        return jsonify({
            "error": "Falha ao obter telemetria.",
            "detail": str(exc)
        }), 500

    resposta = montar_resposta_painel(telem)
    return jsonify(resposta)
