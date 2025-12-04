import time
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

# ============================================================
# GET /api/ativos/<id>/dados-v2 → MODELO REAL DE HORAS
# ============================================================

@api_ativos_bp.get("/<int:id>/dados-v2")
def dados_ativo_v2(id):
    ativo = Ativo.query.get_or_404(id)

    # Buscar telemetria BrasilSat
    try:
        tele = get_telemetria_por_imei(ativo.imei)
    except BrasilSatError as exc:
        return jsonify({"erro": f"Erro BrasilSat: {exc}"}), 500

    motor_ligado = bool(tele.get("motor_ligado"))
    tensao = tele.get("tensao_bateria")
    ts = float(tele.get("servertime") or time.time())
    lat = tele.get("latitude")
    lon = tele.get("longitude")

    # HORAS DE MOTOR vindo direto da BrasilSat
    horas_motor = float(tele.get("horas_motor") or 0.0)

    # OFFSET (valor configurado manualmente)
    offset = float(ativo.horas_offset or 0.0)

    # HORAS DA EMBARCAÇÃO = HORAS MOTOR + OFFSET
    hora_embarcacao = horas_motor + offset

    # =======================================================
    # CÁLCULO DE HORAS PARADAS (motor desligado continuamente)
    # =======================================================
    ultimo_estado = ativo.ultimo_estado_motor
    ultimo_timestamp = ativo.timestamp_evento

    horas_paradas = 0.0

    if ultimo_timestamp is not None:
        if not motor_ligado and ultimo_estado == 0:
            horas_paradas = max(0.0, (ts - float(ultimo_timestamp)) / 3600.0)

    # Salva o novo estado no banco
    ativo.ultimo_estado_motor = 1 if motor_ligado else 0
    ativo.timestamp_evento = ts

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()

    # =======================================================
    # RETORNO COMPLETO QUE O PAINEL PRECISA
    # =======================================================
    return jsonify({
        "id": ativo.id,
        "imei": ativo.imei,

        "monitor_online": True,
        "motor_ligado": motor_ligado,

        "tensao_bateria": tensao,
        "servertime": ts,

        "latitude": lat,
        "longitude": lon,

        "horas_motor": round(horas_motor, 2),
        "horas_offset": round(offset, 2),
        "hora_embarcacao": round(hora_embarcacao, 2),

        "horas_paradas": round(horas_paradas, 2),

        # Ainda não implementado, mas mantemos para não quebrar o painel
        "ignicoes": 0,
        "horas_sistema": 0.0,
    })
