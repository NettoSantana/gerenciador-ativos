import os
import time
import logging
import hashlib
from datetime import datetime

import requests
from flask import jsonify

from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo

logger = logging.getLogger(__name__)

# ============================
#  CONFIG BRASILSAT (ENV VARS)
# ============================

# Pode sobrescrever no Railway, se quiser outro host
BRASILSAT_API_BASE = os.getenv(
    "BRASILSAT_API_BASE",
    "https://api.brasilsatgps.com.br",
).rstrip("/")

# Essas duas você vai configurar como VARIÁVEL DE AMBIENTE no Railway
BRASILSAT_ACCOUNT = os.getenv("BRASILSAT_ACCOUNT")   # login da API
BRASILSAT_PASSWORD = os.getenv("BRASILSAT_PASSWORD") # senha da API (texto puro)

# Cache simples do token em memória
_token_cache = {"token": None, "expires_at": 0.0}


# ============================
#  AUTENTICAÇÃO (authorization)
# ============================


def _get_access_token():
    """
    Faz o fluxo 2.1 da documentação:
    signature = md5( md5(password) + time )
    e retorna o access_token.
    Cacheia em memória até expirar.
    """
    if not BRASILSAT_ACCOUNT or not BRASILSAT_PASSWORD:
        logger.warning("BrasilSat: BRASILSAT_ACCOUNT/BRASILSAT_PASSWORD não configurados.")
        return None

    agora = int(time.time())

    # Usa token em cache se ainda estiver válido
    if _token_cache["token"] and agora < _token_cache["expires_at"]:
        return _token_cache["token"]

    # md5(md5(password) + time)
    pwd_md5 = hashlib.md5(BRASILSAT_PASSWORD.encode("utf-8")).hexdigest()
    signature_src = pwd_md5 + str(agora)
    signature = hashlib.md5(signature_src.encode("utf-8")).hexdigest()

    try:
        resp = requests.get(
            f"{BRASILSAT_API_BASE}/api/authorization",
            params={
                "time": agora,
                "account": BRASILSAT_ACCOUNT,
                "signature": signature,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json() or {}

        if data.get("code") != 0:
            logger.error("BrasilSat auth erro: %s", data)
            return None

        record = data.get("record") or {}
        token = record.get("access_token")
        expires_in = int(record.get("expires_in", 0))

        if not token:
            logger.error("BrasilSat auth: resposta sem access_token.")
            return None

        # Guarda token em cache (deixa uma folga de 5 min)
        _token_cache["token"] = token
        _token_cache["expires_at"] = agora + max(0, expires_in - 300)
        logger.info("BrasilSat auth OK, token obtido.")
        return token

    except Exception as exc:
        logger.error("BrasilSat auth request falhou: %s", exc)
        return None


# ============================
#  TELEMETRIA (track)
# ============================


def fetch_telemetria_externa(ativo: Ativo) -> dict:
    """
    Chama /api/track da BrasilSat para pegar o último ponto do IMEI.
    Faz o mapeamento para o formato que o painel V2 espera.
    """

    imei = getattr(ativo, "imei", None)

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

    token = _get_access_token()
    if not token:
        # Sem token → não tenta API, mas não derruba o painel
        logger.warning("BrasilSat: sem access_token, usando fallback.")
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

    try:
        resp = requests.get(
            f"{BRASILSAT_API_BASE}/api/track",
            params={
                "access_token": token,
                "imeis": imei,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json() or {}

        if data.get("code") != 0:
            logger.error("BrasilSat track erro: %s", data)
            raise RuntimeError("track code != 0")

        records = data.get("record") or []
        if not records:
            logger.warning("BrasilSat track: nenhum registro para IMEI %s", imei)
            raise RuntimeError("sem record")

        # normalmente vem só 1 registro por IMEI
        rec = records[0]

        accstatus = int(rec.get("accstatus", -1))
        motor_ligado = accstatus == 1

        # externalpower vem como string "12.1"
        ext_power_str = (rec.get("externalpower") or "").strip()
        try:
            tensao = float(ext_power_str) if ext_power_str else 0.0
        except ValueError:
            tensao = 0.0

        servertime = int(
            rec.get("servertime")
            or rec.get("systemtime")
            or time.time()
        )

        latitude = float(rec.get("latitude", 0.0) or 0.0)
        longitude = float(rec.get("longitude", 0.0) or 0.0)

        datastatus = int(rec.get("datastatus", 0))
        monitor_online = datastatus == 2  # 2 = OK na doc

        return {
            "imei": imei,
            "monitor_online": monitor_online,
            "motor_ligado": motor_ligado,
            "tensao_bateria": tensao,
            "servertime": servertime,
            "latitude": latitude,
            "longitude": longitude,
        }

    except Exception as exc:
        logger.error("BrasilSat track falhou para ativo %s: %s", ativo.id, exc)
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


# ============================
#  ENDPOINT PRINCIPAL DO PAINEL
#  GET /api/ativos/<id>/dados
# ============================


@api_ativos_bp.get("/<int:id>/dados")
def dados_ativo(id):
    # 1) Busca o ativo no banco
    ativo = Ativo.query.get_or_404(id)

    # 2) Telemetria externa (BrasilSat)
    dados_api = fetch_telemetria_externa(ativo)

    motor_ligado = dados_api["motor_ligado"]

    # 3) Cálculo de horas de sistema (acumuladas + ciclo atual)
    horas_sistema_total = getattr(ativo, "horas_sistema_total", 0) or 0.0
    timestamp_ligado = getattr(ativo, "timestamp_ligado", None)

    if motor_ligado and timestamp_ligado:
        agora_ts = time.time()
        ciclo_horas = max(0.0, (agora_ts - timestamp_ligado) / 3600.0)
        horas_motor = horas_sistema_total + ciclo_horas
    else:
        horas_motor = horas_sistema_total

    # 4) Horas paradas (se não existir no modelo, assume 0)
    horas_paradas = getattr(ativo, "horas_paradas", 0) or 0.0

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
