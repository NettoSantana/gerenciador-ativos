from datetime import datetime

from flask import Blueprint, jsonify

from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.api.monitoramento.brasilsat import (
    get_telemetria_por_imei,
    BrasilSatError,
)

monitoramento_bp = Blueprint("monitoramento", __name__)


@monitoramento_bp.route("/api/ativos/<int:ativo_id>/monitoramento", methods=["GET"])
def obter_monitoramento_ativo(ativo_id: int):
    """
    Endpoint de monitoramento de um ativo específico.

    Fluxo:
    - Busca o Ativo no banco
    - Verifica se há IMEI configurado
    - Chama a BrasilSat para obter telemetria
    - Atualiza campos de monitoramento no modelo Ativo
    - Devolve um JSON consolidado para o frontend
    """
    ativo = Ativo.query.get_or_404(ativo_id)

    if not ativo.imei:
        return (
            jsonify(
                {
                    "erro": "IMEI não configurado para este ativo.",
                    "ativo_id": ativo.id,
                }
            ),
            400,
        )

    try:
        telemetria = get_telemetria_por_imei(ativo.imei)
    except BrasilSatError as exc:
        # Não derruba a aplicação; devolve erro amigável
        return (
            jsonify(
                {
                    "erro": "Falha ao obter telemetria na BrasilSat.",
                    "detalhe": str(exc),
                    "ativo_id": ativo.id,
                }
            ),
            502,
        )

    # Atualiza campos de monitoramento no banco
    ativo.ultima_atualizacao = datetime.utcnow()
    ativo.status_monitoramento = "online"

    # Horas de motor e tensão de bateria vindas da BrasilSat
    horas_motor = telemetria.get("horas_motor")
    if isinstance(horas_motor, (int, float)):
        ativo.horas_motor = float(horas_motor)

    tensao = telemetria.get("tensao_bateria")
    if tensao is not None:
        try:
            ativo.tensao_bateria = float(tensao)
        except (TypeError, ValueError):
            pass

    # Mantém origem como 'brasilsat'
    ativo.origem_dados = "brasilsat"

    db.session.commit()

    # Monta resposta consolidada para o frontend
    resposta = {
        "ativo_id": ativo.id,
        "cliente_id": ativo.cliente_id,
        "nome": ativo.nome,
        "categoria": ativo.categoria,
        "status_monitoramento": ativo.status_monitoramento,
        "ultima_atualizacao": (
            ativo.ultima_atualizacao.isoformat() + "Z"
            if ativo.ultima_atualizacao
            else None
        ),
        "horas_motor": ativo.horas_motor,
        "horas_paradas": ativo.horas_paradas,
        "tensao_bateria": ativo.tensao_bateria,
        "origem_dados": ativo.origem_dados,
        # Dados vindos da BrasilSat:
        "telemetria": {
            k: v for k, v in telemetria.items() if k != "raw"
        },
    }

    return jsonify(resposta), 200
