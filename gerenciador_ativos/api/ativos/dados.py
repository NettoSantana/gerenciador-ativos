from flask import jsonify
from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo
from datetime import datetime
import requests

# ===============================
#   ENDPOINT PRINCIPAL DO PAINEL
# ===============================
# GET /api/ativos/<id>/dados
# ===============================

@api_ativos_bp.get("/<int:id>/dados")
def dados_ativo(id):

    # 1) Busca o ativo no banco
    ativo = Ativo.query.get_or_404(id)

    # 2) Se tiver IMEI ou fonte externa, chamamos API (placeholder por agora)
    # Aqui você conecta a API da BrasilSat / ESP32 / IndFlow
    # ---------------------------------------------------------
    dados_api = {
        "motor_ligado": False,
        "tensao_bateria": 0.0,
        "servertime": int(datetime.utcnow().timestamp()),
        "latitude": 0.0,
        "longitude": 0.0,
        "imei": "N/A"
    }
    
    # (exemplo futuro)
    # r = requests.get(f"http://sua_api.com/device/{ativo.imei}")
    # dados_api = r.json()

    # 3) Cálculo das horas do sistema
    horas_sistema_total = ativo.horas_sistema_total or 0
    timestamp_ligado = ativo.timestamp_ligado

    if dados_api["motor_ligado"]:
        # motor atualmente ligado → somar tempo do ciclo atual
        agora = datetime.utcnow().timestamp()
        horas_ciclo = (agora - (timestamp_ligado or agora)) / 3600
        horas_motor = horas_sistema_total + horas_ciclo
    else:
        # motor desligado → exibe apenas acumulado
        horas_motor = horas_sistema_total

    # 4) Horas paradas (placeholder)
    horas_paradas = ativo.horas_paradas or 0

    # 5) Retorno final do endpoint
    return jsonify({
        "id": ativo.id,
        "nome": ativo.nome,
        "imei": dados_api["imei"],
        "monitor_online": True,  # placeholder
        "motor_ligado": dados_api["motor_ligado"],
        "tensao_bateria": dados_api["tensao_bateria"],
        "servertime": dados_api["servertime"],
        "latitude": dados_api["latitude"],
        "longitude": dados_api["longitude"],
        "horas_motor": round(horas_motor, 2),
        "horas_paradas": round(horas_paradas, 2),
    })
