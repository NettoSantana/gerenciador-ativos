import time
import logging
from flask import jsonify

from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.extensions import db

from gerenciador_ativos.api.monitoramento.brasilsat import (
    get_telemetria_por_imei,
    BrasilSatError,
)

logger = logging.getLogger(__name__)


# ============================================================
#               ENDPOINT PRINCIPAL (/dados)
# ============================================================

@api_ativos_bp.get("/<int:id>/dados")
def dados_ativo(id: int):
    ativo = Ativo.query.get_or_404(id)

    # ===============================
    #   BUSCA TELEMETRIA
    # ===============================
    tele = None
    try:
        if ativo.imei:
            tele = get_telemetria_por_imei(ativo.imei)
    except Exception as exc:
        logger.error(f"[BRASILSAT] erro telemetria ativo {id}: {exc}")
        tele = None

    agora_ts = time.time()

    # ===============================
    #   TELEMETRIA OU MODO OFFLINE
    # ===============================
    if tele:
        monitor_online = True
        motor_ligado = bool(tele.get("motor_ligado"))
        horas_motor_externo = float(tele.get("horas_motor") or 0.0)
        tensao = tele.get("tensao_bateria")
        ts = float(tele.get("servertime") or agora_ts)
        lat = tele.get("latitude")
        lon = tele.get("longitude")
    else:
        monitor_online = False
        motor_ligado = False
        horas_motor_externo = 0.0
        tensao = None
        ts = agora_ts
        lat = None
        lon = None

    # ===============================
    #   HORAS DO SISTEMA (V1)
    # ===============================
    offset = float(ativo.horas_offset or 0.0)
    horas_totais = horas_motor_externo + offset   # FORMATO ANTIGO (LANCHA)

    # ===============================
    #   HORAS PARADAS
    # ===============================
    ultimo_estado = ativo.ultimo_estado_motor
    ultimo_ts = ativo.timestamp_evento

    if ultimo_ts is None:
        horas_paradas = 0.0
    else:
        if (not motor_ligado) and ultimo_estado == 0:
            horas_paradas = max(0.0, (ts - float(ultimo_ts)) / 3600.0)
        else:
            horas_paradas = 0.0

    ativo.ultimo_estado_motor = 1 if motor_ligado else 0
    ativo.timestamp_evento = ts

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    # ===============================
    #   RESPOSTA FORMATO V1 (EXATO)
    # ===============================
    resposta = {
        "id": ativo.id,
        "nome": ativo.nome,
        "imei": ativo.imei,

        "monitor_online": monitor_online,
        "motor_ligado": motor_ligado,

        "tensao_bateria": tensao,
        "servertime": ts,

        "latitude": lat,
        "longitude": lon,

        # HORÍMETRO FORMATO ANTIGO
        "horas_totais": round(horas_totais, 2),
        "offset": round(offset, 2),
        "horimetro": round(horas_totais, 2),

        # PARADAS
        "horas_paradas": round(horas_paradas, 2),

        # CAMPOS USADOS NA V1
        "unidade_base": "horas",
        "medida_base": "h",
    }

    return jsonify(resposta)


# ============================================================
#        ENDPOINT ANTIGO USADO PELO PAINEL (/dados-v2)
# ============================================================

@api_ativos_bp.get("/<int:id>/dados-v2")
def dados_ativo_v2(id: int):
    """
    Compatibilidade total com o painel atual.
    Devolve exatamente o mesmo formato do /dados.
    """
    return dados_ativo(id)
