"""
Integração com a API da BrasilSat para telemetria de ativos.

Uso típico dentro da app:

    from gerenciador_ativos.api.monitoramento.brasilsat import (
        get_telemetria_por_imei,
        BrasilSatError,
    )

    dados = get_telemetria_por_imei(imei="355468593059041")

Este módulo NÃO conhece Flask nem o modelo Ativo.
Ele só:
- autentica na BrasilSat
- busca track por IMEI
- normaliza os dados em um dicionário padrão.
"""

import os
import time
import hashlib
from typing import Tuple, Dict, Any

import requests


# --------------------------------------------------
# Configuração básica
# --------------------------------------------------

BASE_URL = os.getenv("BRASILSAT_BASE_URL", "https://gps.brasilsatgps.com.br")

ACCOUNT = os.getenv("BRASILSAT_ACCOUNT")
PASSWORD = os.getenv("BRASILSAT_PASSWORD")

# Janela de tempo para reaproveitar o token (segundos)
TOKEN_TTL_S = 60 * 20  # 20 minutos


# Cache simples em memória para o token
_TOKEN_CACHE: Dict[str, Any] = {
    "token": None,
    "expires_at": 0.0,
}


# --------------------------------------------------
# Exceções específicas
# --------------------------------------------------

class BrasilSatError(Exception):
    """Erro genérico de integração com a BrasilSat."""


class BrasilSatAuthError(BrasilSatError):
    """Erro de autenticação na BrasilSat."""


class BrasilSatTrackError(BrasilSatError):
    """Erro ao buscar dados de track na BrasilSat."""


# --------------------------------------------------
# Funções internas de utilidade
# --------------------------------------------------

def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise BrasilSatError(
            f"Variável de ambiente obrigatória não definida: {var_name}"
        )
    return value


# --------------------------------------------------
# Autenticação e token
# --------------------------------------------------

def _get_token_from_api() -> Tuple[str, int]:
    """
    Chama a API de autorização da BrasilSat e retorna (token, expires_in_segundos).
    Pode levantar BrasilSatAuthError em caso de falha.
    """
    account = _require_env("BRASILSAT_ACCOUNT")
    password = _require_env("BRASILSAT_PASSWORD")

    now = int(time.time())
    signature = _md5(_md5(password) + str(now))
    url = f"{BASE_URL}/api/authorization"

    try:
        resp = requests.get(
            url,
            params={"time": now, "account": account, "signature": signature},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise BrasilSatAuthError(f"Falha HTTP ao autenticar na BrasilSat: {exc}") from exc

    data = resp.json()
    if data.get("code") != 0:
        raise BrasilSatAuthError(f"Auth falhou: {data}")

    record = data.get("record") or {}
    token = record.get("access_token")
    expires_in = record.get("expires_in", 0)

    if not token:
        raise BrasilSatAuthError(f"Resposta de auth sem access_token: {data}")

    return token, int(expires_in)


def _get_token() -> str:
    """
    Retorna um token válido, usando cache em memória para evitar
    pedir token em toda requisição.
    """
    now = time.time()
    token = _TOKEN_CACHE.get("token")
    expires_at = _TOKEN_CACHE.get("expires_at", 0.0)

    # Se ainda estiver válido, reutiliza
    if token and now < expires_at:
        return token

    # Caso contrário, obtém um novo
    token, expires_in = _get_token_from_api()

    # Margem de segurança (reduz um pouco o TTL)
    ttl_seguro = max(0, expires_in - 60)
    _TOKEN_CACHE["token"] = token
    _TOKEN_CACHE["expires_at"] = now + ttl_seguro

    return token


# --------------------------------------------------
# Track (localização / telemetria)
# --------------------------------------------------

def _track_raw(access_token: str, imei: str) -> Dict[str, Any]:
    """
    Chama a rota /api/track da BrasilSat para um único IMEI
    e devolve o dict bruto (record[0]).

    Pode levantar BrasilSatTrackError.
    """
    url = f"{BASE_URL}/api/track"

    try:
        resp = requests.get(
            url,
            params={"access_token": access_token, "imeis": imei},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise BrasilSatTrackError(f"Falha HTTP em /api/track: {exc}") from exc

    data = resp.json()
    if data.get("code") != 0:
        raise BrasilSatTrackError(f"Track falhou: {data}")

    records = data.get("record") or []
    if not records:
        raise BrasilSatTrackError(f"Nenhum registro retornado para IMEI {imei}")

    return records[0]


def _normalizar_track_bruto(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza o registro bruto em um dicionário mais amigável
    para o restante do sistema.

    Exemplo de campos típicos da BrasilSat (podem variar, por isso defaults):
      - imei
      - accstatus  (0 = motor desligado, 1 = ligado)
      - acctime    (segundos com motor ligado)
      - externalpower (tensão externa em V)
      - servertime (timestamp / string de data/hora)
    """
    imei = record.get("imei")
    accstatus = record.get("accstatus")         # 0/1
    acctime_s = record.get("acctime", 0)        # em segundos
    externalpower_v = record.get("externalpower")
    servertime = record.get("servertime")

    # Interpreta campos
    try:
        acctime_s = float(acctime_s)
    except (TypeError, ValueError):
        acctime_s = 0.0

    horas_motor = acctime_s / 3600.0

    try:
        tensao_bateria = float(externalpower_v) if externalpower_v is not None else None
    except (TypeError, ValueError):
        tensao_bateria = None

    motor_ligado = bool(accstatus == 1)

    return {
        "imei": imei,
        "motor_ligado": motor_ligado,
        "acctime_s": acctime_s,
        "horas_motor": horas_motor,
        "tensao_bateria": tensao_bateria,
        "servertime": servertime,
        "raw": record,  # mantém o bruto para usos futuros, se necessário
    }


# --------------------------------------------------
# Função pública principal
# --------------------------------------------------

def get_telemetria_por_imei(imei: str) -> Dict[str, Any]:
    """
    Função principal para o restante do sistema.

    - Garante token válido (com cache)
    - Chama track para o IMEI informado
    - Normaliza o retorno em um dicionário padrão

    Pode levantar:
      - BrasilSatAuthError
      - BrasilSatTrackError
      - BrasilSatError
    """
    if not imei:
        raise BrasilSatError("IMEI não informado para get_telemetria_por_imei.")

    token = _get_token()
    bruto = _track_raw(token, imei)
    return _normalizar_track_bruto(bruto)


# --------------------------------------------------
# Execução direta para teste manual
# --------------------------------------------------

if __name__ == "__main__":
    # Permite testar rapidamente o módulo em linha de comando:
    #   python -m gerenciador_ativos.api.monitoramento.brasilsat
    imei_teste = os.getenv("BRASILSAT_IMEI")
    if not imei_teste:
        print("Defina BRASILSAT_IMEI para testar.")
    else:
        try:
            dados = get_telemetria_por_imei(imei_teste)
            print("Telemetria BrasilSat OK:")
            for k, v in dados.items():
                if k == "raw":
                    continue
                print(f" - {k}: {v}")
        except BrasilSatError as exc:
            print(f"Erro ao obter telemetria: {exc}")
