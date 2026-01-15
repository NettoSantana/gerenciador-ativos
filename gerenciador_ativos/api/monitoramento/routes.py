"""
Rotas de monitoramento: entrega dados de telemetria para o painel.

Suporta:
- BrasilSat (por IMEI)
- Mobiltracker (por Tracker ID)
"""

import os
import requests
from flask import Blueprint, jsonify
from gerenciador_ativos.api.monitoramento.brasilsat import (
    get_telemetria_por_imei,
    BrasilSatError,
)
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.extensions import db

monitoramento_bp = Blueprint(
    "monitoramento_bp",
    __name__,
    url_prefix="/api/monitoramento"
)

# ------------------------------------------------------------
# CONFIG MOBILTRACKER
# ------------------------------------------------------------

MOBILTRACKER_API_BASE = "https://api.mobiltracker.com.br"
MOBILTRACKER_API_KEY = os.environ.get("MOBILTRACKER_API_KEY")


class MobiltrackerError(Exception):
    pass


def get_localizacao_mobiltracker(tracker_id: str):
    if not MOBILTRACKER_API_KEY:
        raise MobiltrackerError("Chave da API Mobiltracker não configurada.")

    url = f"{MOBILTRACKER_API_BASE}/trackers/{tracker_id}/last-location"
    headers = {
        "Authorization": f"AuthDevice {MOBILTRACKER_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.get(url, headers=headers, timeout=10)

    if resp.status_code != 200:
        raise MobiltrackerError(
            f"Erro Mobiltracker ({resp.status_code}): {resp.text}"
        )

    return resp.json()


# ------------------------------------------------------------
# FUNÇÃO: transformar telemetria crua em JSON para o painel
# ------------------------------------------------------------

def montar_resposta_painel(ativo, telem: dict):
    return {
        "ativo_id": ativo.id,
        "tracking_provider": ativo.tracking_provider,

        # IDENTIFICADOR
        "imei": ativo.imei,
        "tracker_id": ativo.tracker_id,

        # MOTOR (Mobiltracker não fornece)
        "motor_ligado": None,

        # HORAS (calculadas pelo sistema)
        "horas_motor": round((ativo.horas_offset or 0) + (ativo.horas_sistema or 0), 2),

        # BATERIA (Mobiltracker não fornece)
        "tensao_bateria": ativo.tensao_bateria,

        # LOCALIZAÇÃO
        "latitude": telem.get("latitude"),
        "longitude": telem.get("longitude"),

        # TEMPO
        "timestamp": telem.get("time") or telem.get("servertime"),
    }


# ------------------------------------------------------------
# ROTA: pegar dados de monitoramento do ativo
# ------------------------------------------------------------

@monitoramento_bp.route("/<int:ativo_id>/dados", methods=["GET"])
def obter_dados(ativo_id):
    ativo = Ativo.query.filter_by(id=ativo_id, ativo=True).first()

    if not ativo:
        return jsonify({"error": "Ativo não encontrado."}), 404

    try:
        # --------------------------------------------------
        # MOBILTRACKER
        # --------------------------------------------------
        if ativo.tracking_provider == "mobiltracker":
            if not ativo.tracker_id:
                return jsonify({
                    "error": "Ativo não possui Tracker ID cadastrado."
                }), 400

            telem = get_localizacao_mobiltracker(ativo.tracker_id)

            # salva localização no ativo
            ativo.latitude = telem.get("latitude")
            ativo.longitude = telem.get("longitude")
            ativo.ultima_atualizacao = telem.get("time")

            db.session.commit()

            resposta = montar_resposta_painel(ativo, telem)
            return jsonify(resposta)

        # --------------------------------------------------
        # BRASILSAR / IMEI
        # --------------------------------------------------
        if ativo.tracking_provider == "imei":
            if not ativo.imei:
                return jsonify({
                    "error": "Ativo não possui IMEI cadastrado."
                }), 400

            telem = get_telemetria_por_imei(ativo.imei)

            # salva localização no ativo
            ativo.latitude = telem.get("latitude")
            ativo.longitude = telem.get("longitude")
            ativo.ultima_atualizacao = telem.get("servertime")

            db.session.commit()

            resposta = montar_resposta_painel(ativo, telem)
            return jsonify(resposta)

        return jsonify({
            "error": "Provedor de rastreamento desconhecido."
        }), 400

    except (BrasilSatError, MobiltrackerError) as exc:
        return jsonify({
            "error": "Falha ao obter telemetria.",
            "detail": str(exc),
        }), 500
