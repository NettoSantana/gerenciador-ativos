from flask import Blueprint, jsonify
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo

from gerenciador_ativos.api.monitoramento.brasilsat import (
    get_telemetria_por_imei,
    BrasilSatError,
)

api_ativos_dados_bp = Blueprint(
    "api_ativos_dados",
    __name__,
    url_prefix="/api/ativos"
)


@api_ativos_dados_bp.get("/<int:ativo_id>/dados")
def dados_do_ativo(ativo_id):

    ativo = Ativo.query.get(ativo_id)
    if not ativo:
        return jsonify({"erro": "Ativo não encontrado"}), 404

    imei = ativo.imei
    if not imei:
        return jsonify({"erro": "Ativo sem IMEI cadastrado"}), 400

    try:
        tele = get_telemetria_por_imei(imei)
    except BrasilSatError as exc:
        return jsonify({"erro": f"Erro BrasilSat: {exc}"}), 500

    # ------------------------------
    # ESTADO DO MOTOR
    # ------------------------------
    motor_raw = tele.get("motor_ligado")
    motor_ligado = True if str(motor_raw) in ["1", "true", "True"] else False
    estado_atual = 1 if motor_ligado else 0

    # leia o estado anterior do banco corretamente
    estado_anterior = ativo.ultimo_estado_motor  
    if estado_anterior is None:
        estado_anterior = 0

    # ------------------------------
    # IGNIÇÃO CORRETA CRESCENTE
    # ------------------------------
    ignicoes = ativo.total_ignicoes or 0

    # soma só SE houve transição 0→1
    if estado_anterior == 0 and estado_atual == 1:
        ignicoes += 1

    # ------------------------------
    # HORAS / LOCALIZAÇÃO
    # ------------------------------
    horas_motor = tele.get("horas_motor") or 0
    offset = ativo.horas_offset or 0
    horas_embarcacao = offset + horas_motor

    if estado_atual == 0:
        horas_paradas = ativo.horas_paradas or 0
    else:
        horas_paradas = 0

    # ------------------------------
    # SALVAR CORRETAMENTE
    # ------------------------------
    ativo.ultimo_estado_motor = estado_atual
    ativo.total_ignicoes = ignicoes
    ativo.horas_sistema = horas_motor
    ativo.horas_paradas = horas_paradas
    ativo.latitude = tele.get("latitude")
    ativo.longitude = tele.get("longitude")
    ativo.tensao_bateria = tele.get("tensao_bateria")
    ativo.ultima_atualizacao = tele.get("servertime")

    db.session.commit()

    # ------------------------------
    # RESPOSTA
    # ------------------------------
    payload = {
        "ativo_id": ativo.id,
        "nome": ativo.nome,
        "imei": imei,

        "motor_ligado": motor_ligado,
        "horas_motor": horas_motor,
        "offset": offset,
        "horas_embarcacao": horas_embarcacao,
        "horas_paradas": horas_paradas,

        "latitude": tele.get("latitude"),
        "longitude": tele.get("longitude"),
        "velocidade": tele.get("velocidade"),
        "direcao": tele.get("direcao"),

        "tensao_bateria": tele.get("tensao_bateria"),
        "servertime": tele.get("servertime"),

        "ignicoes": ignicoes,
    }

    return jsonify(payload)
