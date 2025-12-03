import time
import logging
from flask import jsonify, request

from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.extensions import db

# Telemetria externa (BrasilSat)
from gerenciador_ativos.api.monitoramento.brasilsat import (
    get_telemetria_por_imei,
    BrasilSatError,
)

logger = logging.getLogger(__name__)

# ============================================================
# FUNÇÃO: Busca telemetria externa da BrasilSat
# ============================================================

def fetch_telemetria_externa(ativo: Ativo) -> dict:
    imei = getattr(ativo, "imei", None)

    if not imei:
        agora = int(time.time())
        return {
            "imei": "N/A",
            "monitor_online": False,
            "motor_ligado": False,
            "tensao_bateria": 0.0,
            "servertime": agora,
            "latitude": 0.0,
            "longitude": 0.0,
        }

    try:
        dados = get_telemetria_por_imei(imei)
    except Exception as exc:
        logger.error("Erro telemetria ativo %s: %s", ativo.id, exc)
        agora = int(time.time())
        return {
            "imei": imei,
            "monitor_online": False,
            "motor_ligado": False,
            "tensao_bateria": 0.0,
            "servertime": agora,
            "latitude": 0.0,
            "longitude": 0.0,
        }

    # Normalização
    motor_ligado = bool(dados.get("motor_ligado", False))

    try:
        tensao_bateria = float(dados.get("tensao_bateria", 0.0))
    except:
        tensao_bateria = 0.0

    try:
        servertime = int(float(dados.get("servertime") or time.time()))
    except:
        servertime = int(time.time())

    try:
        lat = float(dados.get("latitude", 0.0))
    except:
        lat = 0.0

    try:
        lon = float(dados.get("longitude", 0.0))
    except:
        lon = 0.0

    # monitor online (fallback)
    idade = abs(time.time() - servertime)
    monitor_online = idade <= 600  # 10 minutos

    return {
        "imei": imei,
        "monitor_online": monitor_online,
        "motor_ligado": motor_ligado,
        "tensao_bateria": tensao_bateria,
        "servertime": servertime,
        "latitude": lat,
        "longitude": lon,
    }


# ============================================================
# ENDPOINT: GET /api/ativos/<id>/dados  (Painel)
# ============================================================

@api_ativos_bp.get("/<int:id>/dados")
def dados_ativo(id):
    ativo = Ativo.query.get_or_404(id)

    # 1) Telemetria externa
    tele = fetch_telemetria_externa(ativo)
    motor_ligado = tele["motor_ligado"]
    agora_ts = float(tele["servertime"])

    # ======================================================
    # HORÍMETRO INTERNO (horas_sistema_total)
    # ======================================================
    horas_total = float(getattr(ativo, "horas_sistema_total", 0.0) or 0.0)
    ts_ligado = getattr(ativo, "timestamp_ligado", None)
    ts_desligado = getattr(ativo, "timestamp_desligado", None)

    # Motor ligado → acumula horas em tempo real
    if motor_ligado:
        if ts_ligado is None:
            ativo.timestamp_ligado = agora_ts
            ts_ligado = agora_ts
    else:
        if ts_ligado is not None:
            delta = max(0.0, (agora_ts - float(ts_ligado)) / 3600.0)
            horas_total += delta
            ativo.horas_sistema_total = horas_total
            ativo.timestamp_ligado = None
            ts_ligado = None
            ativo.timestamp_desligado = agora_ts
            ts_desligado = agora_ts
        elif ts_desligado is None:
            ativo.timestamp_desligado = agora_ts
            ts_desligado = agora_ts

    try:
        db.session.commit()
    except Exception as exc:
        logger.error("Erro salvando horímetro ativo %s: %s", ativo.id, exc)
        db.session.rollback()

    # Horas em tempo real para exibição
    if motor_ligado and ts_ligado is not None:
        horas_motor = horas_total + max(0.0, (agora_ts - float(ts_ligado)) / 3600.0)
    else:
        horas_motor = horas_total

    # Horas paradas
    if (not motor_ligado) and ts_desligado is not None:
        horas_paradas = max(0.0, (agora_ts - float(ts_desligado)) / 3600.0)
    else:
        horas_paradas = 0.0

    # ======================================================
    # OFFSET (ESCOLHIDO POR VOCÊ)
    # hora_embarcacao = horas_motor + horas_offset
    # ======================================================
    offset = float(ativo.horas_offset or 0.0)
    hora_embarcacao = horas_motor + offset

    # ======================================================
    # RESPOSTA FINAL PRO PAINEL
    # ======================================================
    return jsonify(
        {
            "id": ativo.id,
            "nome": ativo.nome,
            "imei": tele["imei"],
            "monitor_online": tele["monitor_online"],
            "motor_ligado": motor_ligado,
            "tensao_bateria": tele["tensao_bateria"],
            "servertime": tele["servertime"],
            "latitude": tele["latitude"],
            "longitude": tele["longitude"],

            # Horímetros
            "horas_motor": round(horas_motor, 2),
            "horas_offset": round(offset, 2),
            "hora_embarcacao": round(hora_embarcacao, 2),

            "horas_paradas": round(horas_paradas, 2),
        }
    )


# ============================================================
# ENDPOINT: POST /api/ativos/<id>/ajustar-horas
# ============================================================

@api_ativos_bp.post("/<int:id>/ajustar-horas")
def ajustar_horas(id):
    ativo = Ativo.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    # Usuário envia { "offset": 500 }
    try:
        novo_offset = float(data.get("offset"))
    except:
        return jsonify({"erro": "offset inválido"}), 400

    # Atualiza banco
    ativo.horas_offset = novo_offset

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"erro": f"erro ao salvar: {exc}"}), 500

    return jsonify(
        {
            "mensagem": "Offset atualizado com sucesso.",
            "offset": novo_offset,
        }
    ), 200
