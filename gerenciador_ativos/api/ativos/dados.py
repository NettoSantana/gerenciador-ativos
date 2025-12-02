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


# ============================
#  TELEMETRIA (via brasilsat.py)
# ============================

def fetch_telemetria_externa(ativo: Ativo) -> dict:
    """
    Usa o client oficial da BrasilSat (api.monitoramento.brasilsat)
    para obter a telemetria por IMEI e converte para o formato
    que o painel V2 espera.

    Saída padrão:
    {
        "imei": str,
        "monitor_online": bool,
        "motor_ligado": bool,
        "tensao_bateria": float,
        "servertime": int,      # epoch segundos
        "latitude": float,
        "longitude": float,
    }
    """
    imei = getattr(ativo, "imei", None)

    # Sem IMEI: retorna pacote offline
    if not imei:
        logger.warning("Ativo %s sem IMEI configurado.", ativo.id)
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
        # Chama o client unificado
        dados = get_telemetria_por_imei(imei)
    except BrasilSatError as exc:
        logger.error("BrasilSat error para ativo %s (IMEI %s): %s", ativo.id, imei, exc)
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
    except Exception as exc:
        logger.error("Erro inesperado ao obter telemetria BrasilSat para ativo %s: %s", ativo.id, exc)
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

    # ---- Normalização dos campos vindos do client ----
    motor_ligado = bool(dados.get("motor_ligado", False))

    # Tensão de bateria
    tensao_raw = dados.get("tensao_bateria")
    try:
        tensao_bateria = float(tensao_raw) if tensao_raw is not None else 0.0
    except Exception:
        tensao_bateria = 0.0

    # Servertime: força para epoch int
    servertime_raw = dados.get("servertime") or time.time()
    try:
        servertime = int(float(servertime_raw))
    except Exception:
        servertime = int(time.time())

    # Latitude / longitude
    lat_raw = dados.get("latitude")
    lon_raw = dados.get("longitude")
    try:
        latitude = float(lat_raw) if lat_raw is not None else 0.0
    except Exception:
        latitude = 0.0
    try:
        longitude = float(lon_raw) if lon_raw is not None else 0.0
    except Exception:
        longitude = 0.0

    # Monitor online: tenta usar datastatus do "raw" se existir
    raw = dados.get("raw") or {}
    try:
        datastatus = int(raw.get("datastatus", 0))
    except Exception:
        datastatus = 0

    if "datastatus" in raw:
        monitor_online = datastatus == 2
    else:
        # fallback: considera "online" se tem telemetria recente
        idade_seg = max(0, int(time.time()) - servertime)
        monitor_online = idade_seg <= 600  # 10 minutos

    return {
        "imei": imei,
        "monitor_online": monitor_online,
        "motor_ligado": motor_ligado,
        "tensao_bateria": tensao_bateria,
        "servertime": servertime,
        "latitude": latitude,
        "longitude": longitude,
    }


# ============================
#  ENDPOINT PRINCIPAL DO PAINEL
#  GET /api/ativos/<id>/dados
# ============================

@api_ativos_bp.get("/<int:id>/dados")
def dados_ativo(id):
    """
    Endpoint consumido pelo painel do ativo (templates/ativos/painel.html).

    Combina:
    - Telemetria externa (BrasilSat)
    - Horímetro interno (horas_sistema_total + timestamps)
    - Horas paradas (desde o último desligar)
    """
    # 1) Busca o ativo no banco
    ativo = Ativo.query.get_or_404(id)

    # 2) Telemetria externa (BrasilSat, via client único)
    dados_api = fetch_telemetria_externa(ativo)
    motor_ligado = dados_api["motor_ligado"]
    agora_ts = float(dados_api["servertime"] or time.time())

    # -----------------------------
    #  HORÍMETRO (HORAS DO MOTOR)
    # -----------------------------
    # Campos esperados no modelo:
    # - ativo.horas_sistema_total (float, acumulado permanente)
    # - ativo.timestamp_ligado (float, epoch segundos)
    # - ativo.timestamp_desligado (float, epoch segundos)  -> p/ horas paradas

    horas_sistema_total = float(getattr(ativo, "horas_sistema_total", 0.0) or 0.0)
    ts_ligado = getattr(ativo, "timestamp_ligado", None)
    ts_desligado = getattr(ativo, "timestamp_desligado", None)

    # Detecta bordas de estado usando ts_ligado / ts_desligado
    if motor_ligado:
        # Caso 1: motor acabou de ligar (antes não tinha timestamp_ligado)
        if ts_ligado is None:
            # se estava parado, fecha o ciclo de "parado" anterior
            if ts_desligado is not None:
                ativo.timestamp_desligado = None

            ativo.timestamp_ligado = agora_ts
            ts_ligado = agora_ts

    else:
        # motor está desligado
        if ts_ligado is not None:
            # Caso 2: motor acabou de desligar → fecha ciclo de funcionamento
            delta_h = max(0.0, (agora_ts - float(ts_ligado)) / 3600.0)
            horas_sistema_total += delta_h
            ativo.horas_sistema_total = horas_sistema_total
            ativo.timestamp_ligado = None
            ts_ligado = None
            # marca início do período parado
            ativo.timestamp_desligado = agora_ts
            ts_desligado = agora_ts
        elif ts_desligado is None:
            # estava desligado há tempo indeterminado → define referência
            ativo.timestamp_desligado = agora_ts
            ts_desligado = agora_ts

    # Persiste qualquer alteração de estado
    try:
        db.session.commit()
    except Exception as exc:
        logger.error("Erro ao salvar horímetro do ativo %s: %s", ativo.id, exc)
        db.session.rollback()

    # Horas de motor para exibir no painel
    if motor_ligado and ts_ligado is not None:
        # acumulado + tempo desde que ligou
        horas_motor = horas_sistema_total + max(0.0, (agora_ts - float(ts_ligado)) / 3600.0)
    else:
        horas_motor = horas_sistema_total

    # Horas paradas: tempo desde que desligou (não acumulativo, é "há quanto tempo está parado")
    if (not motor_ligado) and ts_desligado is not None:
        horas_paradas = max(0.0, (agora_ts - float(ts_desligado)) / 3600.0)
    else:
        horas_paradas = 0.0

    # 5) Monta resposta final para o painel V2
    return jsonify(
        {
            "id": ativo.id,
            "nome": ativo.nome,
            "imei": dados_api["imei"],
            "monitor_online": dados_api["monitor_online"],
            "motor_ligado": motor_ligado,
            "tensao_bateria": dados_api["tensao_bateria"],
            "servertime": dados_api["servertime"],
            "latitude": dados_api["latitude"],
            "longitude": dados_api["longitude"],
            "horas_motor": round(horas_motor, 2),
            "horas_paradas": round(horas_paradas, 2),
        }
    )
