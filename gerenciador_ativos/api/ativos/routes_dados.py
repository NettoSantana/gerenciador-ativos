from flask import Blueprint, jsonify
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo

# integração BrasilSat
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
        return jsonify({"erro": "Ativo não possui IMEI cadastrado"}), 400

    # Buscar telemetria BrasilSat
    try:
        tele = get_telemetria_por_imei(imei)
    except BrasilSatError as exc:
        return jsonify({"erro": f"Falha ao obter dados da BrasilSat: {exc}"}), 500

    # Normalizar motor
    motor_raw = tele.get("motor_ligado")
    motor_ligado = True if str(motor_raw) in ["1", "true", "True"] else False
    motor_atual = 1 if motor_ligado else 0

    # Horas motor
    horas_motor = tele.get("horas_motor") or 0
    offset = ativo.horas_offset or 0
    horas_embarcacao = offset + horas_motor

    # Horas paradas (NÃO SOMAR VIA GET!)
    horas_paradas = ativo.horas_paradas or 0

    # ============================
    #   IGNIÇÕES — LÓGICA CORRETA
    # ============================
    estado_ant = ativo.ultimo_estado_motor or 0
    ignicoes = ativo.total_ignicoes or 0

    # Somar só quando muda 0 → 1
    if estado_ant == 0 and motor_atual == 1:
        ignicoes += 1

    # ============================

    # Montar payload para enviar ao painel
    payload = {
        "ativo_id": ativo.id,
        "nome": ativo.nome,
        "categoria": ativo.categoria,
        "imei": imei,

        "motor_ligado": motor_ligado,
        "tensao_bateria": tele.get("tensao_bateria"),
        "servertime": tele.get("servertime"),
        "horas_motor": horas_motor,

        "latitude": tele.get("latitude"),
        "longitude": tele.get("longitude"),
        "velocidade": tele.get("velocidade"),
        "direcao": tele.get("direcao"),

        "offset": offset,
        "horas_embarcacao": horas_embarcacao,
        "horas_paradas": horas_paradas,
        "horas_totais": horas_motor,

        "ignicoes": ignicoes,
        "unidade_base": ativo.categoria or "h",
    }

    # SALVAR EM BANCO
    try:
        ativo.horas_sistema = horas_motor
        ativo.ultima_atualizacao = tele.get("servertime")

        ativo.ultimo_estado_motor = motor_atual
        ativo.total_ignicoes = ignicoes

        # salvar horas paradas somente quando outro endpoint tratar isso
        ativo.horas_paradas = horas_paradas

        ativo.latitude = tele.get("latitude")
        ativo.longitude = tele.get("longitude")
        ativo.tensao_bateria = tele.get("tensao_bateria")

        db.session.commit()
    except Exception as e:
        print("ERRO AO SALVAR:", e)

    return jsonify(payload)
