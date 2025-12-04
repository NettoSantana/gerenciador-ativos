import os
import time
import hashlib
from typing import Dict, Any
import requests

# --------------------------------------------------
# CONFIGURAÇÃO DA API BRASILSAT
# --------------------------------------------------

# 🔥 Correção essencial:
# A API real está no subdiretório /V2 — não no domínio raiz.
BASE_URL = os.getenv("BRASILSAT_BASE_URL", "https://gps.brasilsatgps.com.br/V2")

ACCOUNT = os.getenv("BRASILSAT_ACCOUNT")
PASSWORD = os.getenv("BRASILSAT_PASSWORD")


class BrasilSatError(Exception):
    pass


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


# --------------------------------------------------
# OBTÉM ACCESS TOKEN
# --------------------------------------------------

def _obter_access_token() -> str:
    if not ACCOUNT or not PASSWORD:
        raise BrasilSatError("BRASILSAT_ACCOUNT ou BRASILSAT_PASSWORD não definidos.")

    now = int(time.time())
    signature = _md5(_md5(PASSWORD) + str(now))

    url = f"{BASE_URL}/api/authorization"
    params = {"time": now, "account": ACCOUNT, "signature": signature}

    try:
        r = requests.get(url, params=params, timeout=10)
    except Exception as exc:
        raise BrasilSatError(f"Falha de rede ao autenticar: {exc}")

    try:
        data = r.json()
    except:
        raise BrasilSatError(f"Resposta inválida da BrasilSat: {r.text}")

    if data.get("code") != 0:
        raise BrasilSatError(f"Erro na autorização: {data}")

    record = data.get("record") or data.get("data") or {}
    token = record.get("access_token")

    if not token:
        raise BrasilSatError("access_token ausente.")

    return token


# --------------------------------------------------
# BUSCA TRACK (bruto)
# --------------------------------------------------

def _buscar_track_bruto(imei: str) -> Dict[str, Any]:
    if not imei:
        raise BrasilSatError("IMEI não informado.")

    token = _obter_access_token()

    url = f"{BASE_URL}/api/track"
    params = {"access_token": token, "imeis": imei}

    try:
        r = requests.get(url, params=params, timeout=10)
    except Exception as exc:
        raise BrasilSatError(f"Erro de rede em /track: {exc}")

    try:
        data = r.json()
    except:
        raise BrasilSatError(f"Resposta inválida da BrasilSat: {r.text}")

    if data.get("code") != 0:
        raise BrasilSatError(f"Erro na consulta /track: {data}")

    records = data.get("record") or []
    if not records:
        raise BrasilSatError(f"Nenhum registro retornado para IMEI {imei}")

    return records[0]


# --------------------------------------------------
# NORMALIZA TRACK
# --------------------------------------------------

def _normalizar_track_bruto(rec: Dict[str, Any]) -> Dict[str, Any]:
    imei = rec.get("imei")

    acc = rec.get("accstatus")
    acctime = float(rec.get("acctime") or 0)
    horas_motor = acctime / 3600.0

    tensao = rec.get("externalpower")
    try:
        tensao = float(tensao) if tensao else None
    except:
        tensao = None

    lat = rec.get("latitude") or rec.get("lat")
    lon = rec.get("longitude") or rec.get("lng")

    try:
        lat = float(lat) if lat else None
        lon = float(lon) if lon else None
    except:
        lat = lon = None

    return {
        "imei": imei,
        "motor_ligado": (acc == 1),
        "acctime_s": acctime,
        "horas_motor": horas_motor,
        "tensao_bateria": tensao,
        "servertime": rec.get("servertime"),
        "latitude": lat,
        "longitude": lon,
        "raw": rec,
    }


# --------------------------------------------------
# FUNÇÃO PÚBLICA
# --------------------------------------------------

def get_telemetria_por_imei(imei: str) -> Dict[str, Any]:
    bruto = _buscar_track_bruto(imei)
    return _normalizar_track_bruto(bruto)


# --------------------------------------------------
# TESTE MANUAL
# --------------------------------------------------

if __name__ == "__main__":
    imei = os.getenv("BRASILSAT_IMEI")
    if not imei:
        print("Defina BRASILSAT_IMEI")
    else:
        print(get_telemetria_por_imei(imei))
