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

    # --- BrasilSat ---
    try:
        tele = get_telemetria_por_imei(imei)
    except BrasilSatError as exc:
        return jsonify({"erro": f"Falha ao obter dados da BrasilSat: {exc}"}), 500

    # ---------------- MOTOR ----------------
    motor_raw = tele.get("motor_ligado")
    motor_ligado = True if str(motor_raw) in ["1", "true", "True"] else False
    motor_atual = 1 if motor_ligado else 0

    estado_anterior = ativo.ultimo_estado_motor
    if estado_anterior is None:
        estado_anterior = motor_atual  # evita falsa ignição na primeira leitura

    # ---------------- IGNIÇÕES ----------------
    ignicoes = ativo.total_ignicoes or 0

    mudou_de_0_para_1 = (estado_anterior == 0 and motor_atual == 1)

    if mudou_de_0_para_1:
        ignicoes += 1

    # ---------------- HORAS ----------------
    horas_motor = tele.get("horas_motor") or 0
    offset = ativo.horas_offset or 0
    horas_embarcacao = offset + horas_motor

    # Horas paradas NÃO devem zerar sempre
    if motor_atual == 0:
        horas_paradas = ativo.horas_paradas or 0
    else:
        horas_paradas = 0

    # ---------------- LOCALIZAÇÃO ----------------
    lat = tele.get("latitude")
    lon = tele.get("longitude")

    # ---------------- SALVAR ----------------
    try:
        # salvar SOMENTE se telemetria válida
        ativo.horas_sistema = horas_motor
        ativo.ultima_atualizacao = tele.get("servertime")

        if mudou_de_0_para_1 or estado_anterior != motor_atual:
            ativo.ultimo_estado_motor = motor_atual

        ativo.horas_paradas = horas_paradas
        ativo.latitude = lat
        ativo.longitude = lon
        ativo.tensao_bateria = tele.get("tensao_bateria")
        ativo.total_ignicoes = ignicoes

        db.session.commit()

    except Exception as e:
        print("ERRO AO SALVAR:", e)

    # ---------------- RETORNO ----------------
    payload = {
        "ativo_id": ativo.id,
        "nome": ativo.nome,
        "categoria": ativo.categoria,
        "imei": imei,

        "motor_ligado": motor_ligado,
        "tensao_bateria": tele.get("tensao_bateria"),
        "servertime": tele.get("servertime"),

        "horas_motor": horas_motor,
        "offset": offset,
        "horas_embarcacao": horas_embarcacao,
        "horas_paradas": horas_paradas,

        "latitude": lat,
        "longitude": lon,
        "velocidade": tele.get("velocidade"),
        "direcao": tele.get("direcao"),

        "ignicoes": ignicoes,
        "unidade_base": ativo.categoria or "h",
    }

    return jsonify(payload)
