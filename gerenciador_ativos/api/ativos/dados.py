from datetime import datetime
import os
import logging

import requests
from flask import jsonify

from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo


logger = logging.getLogger(__name__)

# Config da API externa (BrasilSat / ESP32 / IndFlow etc.)
BRASILSAT_BASE_URL = os.getenv("BRASILSAT_BASE_URL", "").rstrip("/")
BRASILSAT_TOKEN = os.getenv("BRASILSAT_TOKEN", "")


def fetch_telemetria_externa(ativo: Ativo) -> dict:
    """
    Busca os dados mais recentes do rastreador / API externa para este ativo.
    Ajuste a URL, parâmetros e mapeamento conforme a API real.
    Retorna sempre um dicionário com as chaves usadas pelo painel.
    """

    imei = getattr(ativo, "imei", None)
    if not imei or not BRASILSAT_BASE_URL or not BRASILSAT_TOKEN:
        # Sem IMEI ou sem config → devolve defaults
        logger.warning("Telemetria externa desabilitada para ativo %s", ativo.id)
        agora = int(datetime.utcnow().timestamp())
        return {
            "imei": imei or "N/A",
            "motor_ligado": False,
            "tensao_bateria": 0.0,
            "servertime": agora,
            "latitude": 0.0,
            "longitude": 0.0,
        }

    try:
        # 🔧 AJUSTE AQUI conforme sua API real
        # Exemplo genérico:
        resp = requests.get(
            f"{BRASILSAT_BASE_URL}/dados",
            params={"imei": imei, "token": BRASILSAT_TOKEN},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json() or {}

        # Mapeamento genérico → adapte para os campos reais da sua API
        return {
            "imei": imei,
            "motor_ligado": bool(data.get("motor_ligado", False)),
            "tensao_bateria": float(data.get("tensao_bateria", 0.0)),
            "servertime": int(data.get("servertime", datetime.utcnow().timestamp())),
            "latitude": float(data.get("latitude", 0.0)),
            "longitude": float(data.get("longitude", 0.0)),
        }

    except Exception as exc:
        logger.error("Erro ao consultar API externa para ativo %s: %s", ativo.id, exc)
        agora = int(datetime.utcnow().timestamp())
        # Fallback seguro
        return {
            "imei": imei,
            "motor_ligado": False,
            "tensao_bateria": 0.0,
            "servertime": agora,
            "latitude": 0.0,
            "longitude": 0.0,
        }


# ===============================
#   ENDPOINT PRINCIPAL DO PAINEL
# ===============================
# GET /api/ativos/<id>/dados
# ===============================

@api_ativos_bp.get("/<int:id>/dados")
def dados_ativo(id):
    # 1) Busca o ativo no banco
    ativo = Ativo.query.get_or_404(id)

    # 2) Busca telemetria na API externa
    dados_api = fetch_telemetria_externa(ativo)

    # 3) Cálculo das horas do sistema (acumulado + ciclo atual)
    horas_sistema_total = getattr(ativo, "horas_sistema_total", 0) or 0
    timestamp_ligado = getattr(ativo, "timestamp_ligado", None)

    motor_ligado = dados_api["motor_ligado"]

    if motor_ligado and timestamp_ligado:
        agora_ts = datetime.utcnow().timestamp()
        ciclo_horas = max(0.0, (agora_ts - timestamp_ligado) / 3600.0)
        horas_motor = horas_sistema_total + ciclo_horas
    else:
        horas_motor = horas_sistema_total

    # 4) Horas paradas (se ainda não existir no modelo, cai para 0)
    horas_paradas = getattr(ativo, "horas_paradas", 0) or 0

    # 5) Monta resposta final para o painel
    return jsonify(
        {
            "id": ativo.id,
            "nome": ativo.nome,
            "imei": dados_api["imei"],
            "monitor_online": True,  # você pode amarrar isso ao sucesso da API
            "motor_ligado": motor_ligado,
            "tensao_bateria": dados_api["tensao_bateria"],
            "servertime": dados_api["servertime"],
            "latitude": dados_api["latitude"],
            "longitude": dados_api["longitude"],
            "horas_motor": round(horas_motor, 2),
            "horas_paradas": round(horas_paradas, 2),
        }
    )
