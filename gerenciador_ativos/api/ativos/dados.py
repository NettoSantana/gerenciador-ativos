import time
import logging
from flask import jsonify, request

from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.extensions import db

# Telemetria BrasilSat
from gerenciador_ativos.api.monitoramento.brasilsat import (
    get_telemetria_por_imei,
    BrasilSatError,
)

logger = logging.getLogger(__name__)


# ============================================================
# GET /api/ativos/<id>/dados-v2  → MODELO A COMPLETO
# ============================================================

@api_ativos_bp.get("/<int:id>/dados-v2")
def dados_ativo_v2(id):
    ativo = Ativo.query.get_or_404(id)

    # Buscar telemetria BrasilSat
    try:
        tele = get_telemetria_por_imei(ativo.imei)
    except Exception as exc:
        logger.error(f"Erro BrasilSat: {exc}")
        return jsonify({"erro": "Falha ao obter telemetria"}), 500

    motor_ligado = bool(tele.get("motor_ligado"))
    horas_motor = float(tele.get("horas_motor") or 0.0)  # valor oficial BrasilSat
    tensao = tele.get("tensao_bateria")
    latitude = tele.get("latitude")
    longitude = tele.get("longitude")

    ts = float(tele.get("servertime") or time.time())

    # ======================================================
    # HORAS DA EMBARCAÇÃO = horas_motor + offset
    # ======================================================
    offset = float(ativo.horas_offset or 0.0)
    hora_embarcacao = horas_motor + offset

    # ======================================================
    # CÁLCULO DAS HORAS PARADAS
    # ======================================================

    ultimo_estado = ativo.ultimo_estado_motor
    ultimo_ts = ativo.timestamp_evento

    if ultimo_ts is None:
        horas_paradas = 0.0
    else:
        if (not motor_ligado) and ultimo_estado == 0:
            horas_paradas = max(0.0, (ts - float(ultimo_ts)) / 3600.0)
        else:
            horas_paradas = 0.0

    # ======================================================
    # ATUALIZAÇÃO DO BANCO
    # ======================================================
    ativo.ultimo_estado_motor = 1 if motor_ligado else 0
    ativo.timestamp_evento = ts
    ativo.latitude = latitude
    ativo.longitude = longitude
    ativo.tensao_bateria = tensao

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f"Erro ao salvar estado: {exc}")

    # ======================================================
    # RETORNO PARA O PAINEL
    # ======================================================
    return jsonify({
        "id": ativo.id,
        "nome": ativo.nome,
        "imei": ativo.imei,

        "monitor_online": True,
        "motor_ligado": motor_ligado,

        "tensao_bateria": tensao,
        "servertime": ts,

        "latitude": latitude,
        "longitude": longitude,

        # HORAS MODELO A
        "horas_motor": round(horas_motor, 2),
        "horas_offset": round(offset, 2),
        "hora_embarcacao": round(hora_embarcacao, 2),

        # HORAS PARADAS ATUALIZADAS
        "horas_paradas": round(horas_paradas, 2),
    })


# ============================================================
# POST /api/ativos/<id>/ajustar-horas
# ============================================================

@api_ativos_bp.post("/<int:id>/ajustar-horas")
def ajustar_horas(id):
    ativo = Ativo.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    try:
        offset = float(data.get("offset"))
    except:
        return jsonify({"erro": "offset inválido"}), 400

    ativo.horas_offset = offset

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"erro": str(exc)}), 500

    return jsonify({
        "mensagem": "Offset atualizado",
        "offset": offset
    })
