from flask import Blueprint, jsonify
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo

# integração BrasilSat da V2 (já existente)
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
    """
    Retorna os dados de telemetria do ativo especificado,
    no mesmo formato usado na V1 (painel interno).
    """

    # 1) Buscar o ativo no banco
    ativo = Ativo.query.get(ativo_id)
    if not ativo:
        return jsonify({"erro": "Ativo não encontrado"}), 404

    # 2) Precisa ter IMEI
    imei = ativo.imei
    if not imei:
        return jsonify({"erro": "Ativo não possui IMEI cadastrado"}), 400

    # 3) Buscar telemetria da BrasilSat
    try:
        tele = get_telemetria_por_imei(imei)
    except BrasilSatError as exc:
        return jsonify({"erro": f"Falha ao obter dados da BrasilSat: {exc}"}), 500

    # 4) Montar payload no padrão da V1
    payload = {
        "ativo_id": ativo.id,
        "nome": ativo.nome,
        "categoria": ativo.categoria,
        "imei": imei,

        # telemetria
        "motor_ligado": tele.get("motor_ligado"),
        "tensao_bateria": tele.get("tensao_bateria"),
        "servertime": tele.get("servertime"),
        "horas_motor": tele.get("horas_motor"),

        # localização
        "latitude": tele.get("latitude"),
        "longitude": tele.get("longitude"),
        "velocidade": tele.get("velocidade"),
        "direcao": tele.get("direcao"),

        # compatibilidade com o painel
        "unidade_base": ativo.categoria or "h",
        "horas_totais": ativo.horas_sistema or 0,
        "offset": ativo.horas_offset or 0,

        # campos extras do banco se quiser usar depois
        "horas_paradas": ativo.horas_paradas or 0,
    }

    # 5) Atualizar valores do banco (opcional, mas recomendado)
    try:
        ativo.horas_sistema = tele.get("horas_motor") or ativo.horas_sistema
        ativo.ultima_atualizacao = tele.get("servertime")
        ativo.horas_paradas = ativo.horas_paradas  # se quiser incorporar lógica da V1 depois
        ativo.ultimo_estado_motor = 1 if tele.get("motor_ligado") else 0
        ativo.latitude = tele.get("latitude")
        ativo.longitude = tele.get("longitude")
        ativo.horas_offset = ativo.horas_offset  # mantido
        ativo.tensao_bateria = tele.get("tensao_bateria")

        db.session.commit()
    except Exception:
        # falha ao atualizar o banco não deve impedir retorno
        pass

    return jsonify(payload)
