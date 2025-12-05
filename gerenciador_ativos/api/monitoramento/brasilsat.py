"""
Integração com a API da BrasilSat para telemetria de ativos.

Responsabilidades deste módulo:
- autenticar na BrasilSat
- buscar o último track por IMEI
- normalizar os dados em um dicionário amigável

Uso típico dentro da app:

    from gerenciador_ativos.api.monitoramento.brasilsat import (
        get_telemetria_por_imei,
        BrasilSatError,
    )

    dados = get_telemetria_por_imei(imei="355468593059041")
"""

import os
import time
import hashlib
from typing import Dict, Any

import requests


# --------------------------------------------------
# Configuração básica
# --------------------------------------------------

BASE_URL = os.getenv("BRASILSAT_BASE_URL", "https://gps.brasilsatgps.com.br")
ACCOUNT = os.getenv("BRASILSAT_ACCOUNT")
PASSWORD = os.getenv("BRASILSAT_PASSWORD")


class BrasilSatError(Exception):
    """Erro genérico de integração com a BrasilSat."""


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


# --------------------------------------------------
# Autenticação
# --------------------------------------------------

def _obter_access_token() -> str:
    """
    Obtém um access_token na BrasilSat.
    Endpoint:
        GET /api/authorization?time=...&account=...&signature=...
    """

    if not ACCOUNT or not PASSWORD:
        raise BrasilSatError("BRASILSAT_ACCOUNT ou BRASILSAT_PASSWORD não definidos no ambiente.")

    now = int(time.time())
    signature = _md5(_md5(PASSWORD) + str(now))

    url = f"{BASE_URL}/api/authorization"
    params = {
        "time": now,
        "account": ACCOUNT,
        "signature": signature,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.RequestException as exc:
        raise BrasilSatError(f"Falha de rede ao autenticar: {exc}") from exc

    try:
        data = resp.json()
    except Exception:
        raise BrasilSatError(f"Resposta inválida: {resp.text}")

    if data.get("code") != 0:
        raise BrasilSatError(f"Erro na autorização BrasilSat: {data}")

    record = data.get("record") or data.get("data") or {}
    token = record.get("access_token")

    if not token:
        raise BrasilSatError(f"access_token ausente: {data}")

    return token


# --------------------------------------------------
# Track por IMEI (COM LOCALIZAÇÃO)
# --------------------------------------------------

def _buscar_track_bruto(imei: str) -> Dict[str, Any]:
    """
    Versão oficial que usa o endpoint COMPLETO:
        /api/track/info
    Este endpoint traz latitude, longitude, velocidade etc.
    """

    if not imei:
        raise BrasilSatError("IMEI não informado para busca de track.")

    access_token = _obter_access_token()

    #🔥 AQUI ESTÁ A CORREÇÃO REAL
    url = f"{BASE_URL}/api/track/info"

    params = {
        "access_token": access_token,
        "imeis": imei,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
    except requests.RequestException as exc:
        raise BrasilSatError(f"Falha de rede em /api/track/info: {exc}") from exc

    try:
        data = resp.json()
    except ValueError:
        raise BrasilSatError(f"Resposta inválida da BrasilSat em /track/info: {resp.text}")

    if data.get("code") != 0:
        raise BrasilSatError(f"Erro BrasilSat /track/info: {data}")

    records = data.get("record") or []
    if not records:
        raise BrasilSatError(f"Nenhum registro retornado para IMEI {imei}: {data}")

    return records[0]


# --------------------------------------------------
# Normalização do track
# --------------------------------------------------

def _normalizar_track_bruto(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte o JSON bruto em um dicionário padronizado.
    Agora inclui latitude, longitude, velocidade e direção.
    """

    imei = record.get("imei")

    # -------------------------
    # STATUS DO MOTOR
    # -------------------------
    accstatus = record.get("accstatus")
    acctime_s = record.get("acctime", 0)
    externalpower_v = record.get("externalpower")
    servertime = record.get("servertime")

    # -------------------------
    # LOCALIZAÇÃO
    # -------------------------
    lat = (
        record.get("latitude")
        or record.get("lat")
        or record.get("gpslat")
        or None
    )

    lon = (
        record.get("longitude")
        or record.get("lng")
        or record.get("lon")
        or record.get("gpslon")
        or None
    )

    speed = record.get("speed") or record.get("gps_speed") or None
    course = record.get("course") or record.get("direction") or None

    # -------------------------
    # Conversões
    # -------------------------
    try:
        acctime_s = float(acctime_s)
    except:
        acctime_s = 0

    horas_motor = acctime_s / 3600.0

    try:
        tensao_bateria = float(externalpower_v) if externalpower_v is not None else None
    except:
        tensao_bateria = None

    motor_ligado = bool(accstatus == 1)

    # Latitude / longitude
    try:
        lat = float(lat)
    except:
        lat = None

    try:
        lon = float(lon)
    except:
        lon = None

    try:
        speed = float(speed)
    except:
        speed = None

    return {
        "imei": imei,
        "motor_ligado": motor_ligado,

        "acctime_s": acctime_s,
        "horas_motor": horas_motor,

        "tensao_bateria": tensao_bateria,
        "servertime": servertime,

        # 🔥 CAMPOS QUE INTERESSAM AO SEU PAINEL
        "latitude": lat,
        "longitude": lon,
        "velocidade": speed,
        "direcao": course,

        # Útil para debug quando precisar
        "raw": record,
    }


# --------------------------------------------------
# Função pública
# --------------------------------------------------

def get_telemetria_por_imei(imei: str) -> Dict[str, Any]:
    bruto = _buscar_track_bruto(imei)
    return _normalizar_track_bruto(bruto)


# --------------------------------------------------
# Execução direta para teste manual
# --------------------------------------------------

if __name__ == "__main__":
    imei_teste = os.getenv("BRASILSAT_IMEI")
    if not imei_teste:
        print("Defina BRASILSAT_IMEI para testar.")
    else:
        try:
            dados = get_telemetria_por_imei(imei_teste)
            print("Telemetria BrasilSat OK:")
            for k, v in dados.items():
                if k != "raw":
                    print(f" - {k}: {v}")
        except BrasilSatError as exc:
            print(f"Erro ao obter telemetria: {exc}")
