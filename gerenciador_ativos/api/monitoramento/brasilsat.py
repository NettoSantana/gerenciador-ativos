import requests
import time

class BrasilSatError(Exception):
    pass


URL_BRASILSAT = "https://api.brasilsat.com.br/telemetria"


def get_telemetria_por_imei(imei: str) -> dict:
    """
    Consulta a BrasilSat e normaliza todos os campos.
    """
    try:
        response = requests.get(f"{URL_BRASILSAT}/{imei}", timeout=8)
    except Exception as exc:
        raise BrasilSatError(f"Erro de conexão: {exc}")

    if response.status_code != 200:
        raise BrasilSatError(f"HTTP {response.status_code}: {response.text}")

    bruto = response.json() or {}
    return _normalizar_track_bruto(bruto)


# =====================================================================
# NORMALIZAÇÃO TOTAL
# =====================================================================

def _normalizar_track_bruto(d: dict) -> dict:
    """
    Normaliza os campos do pacote BrasilSat.
    MODELO A — HORAS REAIS DO MOTOR (hodômetro fixo)
    """

    # --- Accstatus → motor ligado ---
    acc = str(d.get("accstatus", 0)).strip()
    motor_ligado = acc in ["1", "true", "True"]

    # --- Horas motor (HODÔMETRO REAL) ---
    # acctime é SEMPRE acumulado desde que instalou
    try:
        acctime_s = float(d.get("acctime", 0))
    except:
        acctime_s = 0.0

    horas_motor = acctime_s / 3600.0

    # --- Tensão ---
    try:
        vbatt = float(d.get("vbatt", 0.0))
    except:
        vbatt = 0.0

    # --- Tempo do servidor ---
    try:
        servertime = int(float(d.get("servertime", time.time())))
    except:
        servertime = int(time.time())

    # --- Latitude / Longitude ---
    try:
        lat = float(d.get("lat", 0))
    except:
        lat = 0.0

    try:
        lng = float(d.get("lng", 0))
    except:
        lng = 0.0

    # --- Velocidade ---
    try:
        vel = float(d.get("speed", 0))
    except:
        vel = 0.0

    # --- Direção ---
    try:
        direcao = float(d.get("course", 0))
    except:
        direcao = 0.0

    # ==============================================================
    # RETORNO FINAL NORMALIZADO
    # ==============================================================

    return {
        "motor_ligado": motor_ligado,
        "horas_motor": horas_motor,
        "tensao_bateria": vbatt,
        "servertime": servertime,
        "latitude": lat,
        "longitude": lng,
        "velocidade": vel,
        "direcao": direcao,
    }
import logging
from flask import jsonify, request

from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.extensions import db

from gerenciador_ativos.api.monitoramento.brasilsat import (
    get_telemetria_por_imei,
    BrasilSatError,
)

logger = logging.getLogger(__name__)


# ========================================================================
# GET /api/ativos/<id>/dados     → usado pelo painel
# ========================================================================

@api_ativos_bp.get("/<int:id>/dados")
def dados_ativo(id):
    ativo = Ativo.query.get_or_404(id)

    # ------------------------------
    # TELEMETRIA BRASILSAT
    # ------------------------------
    try:
        tele = get_telemetria_por_imei(ativo.imei)
    except BrasilSatError as exc:
        return jsonify({"erro": str(exc)}), 500

    motor_ligado = tele["motor_ligado"]
    horas_motor = tele["horas_motor"]             # HODÔMETRO REAL
    offset = float(ativo.horas_offset or 0)
    horas_embarcacao = horas_motor + offset       # regra definida

    # ------------------------------
    # HORAS PARADAS
    # ------------------------------
    horas_paradas = 0.0 if motor_ligado else (float(ativo.horas_paradas or 0))

    # ------------------------------
    # ATUALIZAÇÕES NO BANCO
    # ------------------------------
    try:
        ativo.horas_sistema_total = horas_motor
        ativo.ultimo_estado_motor = 1 if motor_ligado else 0
        ativo.horas_paradas = horas_paradas
        ativo.latitude = tele["latitude"]
        ativo.longitude = tele["longitude"]
        ativo.tensao_bateria = tele["tensao_bateria"]
        ativo.ultima_atualizacao = tele["servertime"]
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f"Erro salvando ativo {ativo.id}: {exc}")

    # ------------------------------
    # RETORNO AO PAINEL
    # ------------------------------
    return jsonify(
        {
            "id": ativo.id,
            "nome": ativo.nome,
            "imei": ativo.imei,

            "motor_ligado": motor_ligado,
            "horas_motor": round(horas_motor, 2),
            "horas_offset": round(offset, 2),
            "horas_embarcacao": round(horas_embarcacao, 2),

            "horas_paradas": round(horas_paradas, 2),

            "tensao_bateria": tele["tensao_bateria"],
            "servertime": tele["servertime"],
            "latitude": tele["latitude"],
            "longitude": tele["longitude"],
            "velocidade": tele["velocidade"],
            "direcao": tele["direcao"],
        }
    )


# ========================================================================
# POST /api/ativos/<id>/ajustar-horas     → botão do painel
# ========================================================================

@api_ativos_bp.post("/<int:id>/ajustar-horas")
def ajustar_horas(id):
    ativo = Ativo.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    try:
        novo_offset = float(data.get("offset"))
    except:
        return jsonify({"erro": "offset inválido"}), 400

    ativo.horas_offset = novo_offset

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"erro": str(exc)}), 500

    return jsonify(
        {"mensagem": "Offset atualizado com sucesso.", "offset": novo_offset}
    ), 200
