import requests
import time

# ==============================
#   CONFIG BRASILSAT
# ==============================

BRASILSAT_URL = "https://gps.brasilsatgps.com.br/V2/api/device/lastposition"
BRASILSAT_USER = "admin"
BRASILSAT_PASS = "123456"

class BrasilSatError(Exception):
    pass


# ==============================
#   FUNÇÃO PRINCIPAL
# ==============================

def get_telemetria_por_imei(imei: str):
    """
    Consulta a última posição/telemetria de um dispositivo BrasilSat.
    Retorna sempre um dicionário padronizado.
    """

    if not imei:
        raise BrasilSatError("IMEI não informado")

    try:
        resp = requests.get(
            BRASILSAT_URL,
            params={"login": BRASILSAT_USER, "password": BRASILSAT_PASS, "imei": imei},
            timeout=10
        )
    except Exception as exc:
        raise BrasilSatError(f"Falha de conexão: {exc}")

    if resp.status_code != 200:
        raise BrasilSatError(f"HTTP {resp.status_code}: {resp.text}")

    try:
        data = resp.json()
    except:
        raise BrasilSatError("Resposta inválida da API BrasilSat")

    # ==============================
    # Normalização dos campos
    # ==============================

    tele = {
        "motor_ligado": bool(data.get("ignicao")),
        "tensao_bateria": data.get("tensao_bateria"),
        "servertime": float(data.get("servertime") or time.time()),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),

        # Horas de motor (acctime da BrasilSat)
        "horas_motor": float(data.get("acctime") or 0.0),
    }

    return tele
