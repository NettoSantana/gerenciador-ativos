import time
import logging
from flask import jsonify

from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.extensions import db

# Telemetria BrasilSat
from gerenciador_ativos.api.monitoramento.brasilsat import (
    get_telemetria_por_imei,
    BrasilSatError,
)

logger = logging.getLogger(__name__)


@api_ativos_bp.get("/<int:id>/dados")
def dados_ativo(id: int):
    """
    Endpoint principal consumido pelo painel.

    Sempre devolve 200 com um JSON “amigável” pro front, mesmo que a BrasilSat
    esteja fora do ar. Se a telemetria falhar, cai em modo offline.
    """
    ativo = Ativo.query.get_or_404(id)

    # -----------------------------
    # 1) TENTAR BUSCAR TELEMETRIA
    # -----------------------------
    tele = None
    try:
        if ativo.imei:
            tele = get_telemetria_por_imei(ativo.imei)
    except BrasilSatError as exc:
        logger.error(f"[BRASILSAT] Erro ao obter telemetria para ativo {id}: {exc}")
        tele = None
    except Exception as exc:  # qualquer outra coisa inesperada
        logger.exception(
            f"[BRASILSAT] Erro inesperado ao obter telemetria para ativo {id}"
        )
        tele = None

    # -----------------------------
    # 2) DADOS BÁSICOS
    # -----------------------------
    agora_ts = time.time()

    if tele:
        monitor_online = True
        motor_ligado = bool(tele.get("motor_ligado"))
        horas_motor_externo = float(tele.get("horas_motor") or 0.0)
        tensao = tele.get("tensao_bateria")
        ts = float(tele.get("servertime") or agora_ts)
        lat = tele.get("latitude")
        lon = tele.get("longitude")
    else:
        # Modo "offline": sem leitura válida
        monitor_online = False
        motor_ligado = False
        horas_motor_externo = 0.0
        tensao = None
        ts = agora_ts
        lat = None
        lon = None

    # -----------------------------
    # 3) CÁLCULO HORÍMETRO OFICIAL
    # -----------------------------
    offset = float(ativo.horas_offset or 0.0)
    hora_embarcacao = horas_motor_externo + offset

    # -----------------------------
    # 4) HORAS PARADAS
    # -----------------------------
    ultimo_estado = ativo.ultimo_estado_motor
    ultimo_ts = ativo.timestamp_evento

    if ultimo_ts is None:
        horas_paradas = 0.0
    else:
        if (not motor_ligado) and ultimo_estado == 0:
            # motor já estava desligado antes → acumula tempo
            horas_paradas = max(0.0, (ts - float(ultimo_ts)) / 3600.0)
        else:
            # ligou agora ou está ligado → zera contador
            horas_paradas = 0.0

    # Atualiza estado atual no banco (mas não deixamos o painel quebrar
    # se o commit der erro).
    ativo.ultimo_estado_motor = 1 if motor_ligado else 0
    ativo.timestamp_evento = ts
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f"Erro ao salvar estado do motor do ativo {id}: {exc}")

    # -----------------------------
    # 5) MONTA RESPOSTA PRO FRONT
    # -----------------------------
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

        # Horímetro vindo do rastreador
        "horas_motor": round(horas_motor_externo, 2),

        # Ajustes da embarcação
        "horas_offset": round(offset, 2),
        "hora_embarcacao": round(hora_embarcacao, 2),

        # Horas paradas acumuladas
        "horas_paradas": round(horas_paradas, 2),

        # Campo que o front já conhece, mesmo que hoje seja 0
        "horas_sistema": 0.0,
        "ignicoes": 0,
    }

    return jsonify(resposta)
