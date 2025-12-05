from flask import request, jsonify
from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.extensions import db


@api_ativos_bp.post("/<int:id>/offset")
def atualizar_offset(id):
    """
    Atualiza o offset manual do horímetro da embarcação.
    Espera JSON:
    {
        "offset": 123.4
    }
    """

    ativo = Ativo.query.get_or_404(id)

    data = request.get_json(silent=True) or {}
    novo_offset = data.get("offset")

    # validação
    try:
        novo_offset = float(novo_offset)
    except (TypeError, ValueError):
        return jsonify({"erro": "offset inválido"}), 400

    # salva no banco
    ativo.horas_offset = novo_offset
    db.session.commit()

    return jsonify({
        "mensagem": "offset atualizado com sucesso",
        "ativo_id": ativo.id,
        "offset": novo_offset
    })
