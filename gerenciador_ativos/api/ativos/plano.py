from flask import request, jsonify

from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.preventiva_models import PreventivaItem
from gerenciador_ativos.extensions import db


@api_ativos_bp.get("/<int:id>/plano")
def listar_plano(id):
    """Lista o plano de preventiva cadastrado para o ativo."""
    ativo = Ativo.query.get_or_404(id)
    itens = PreventivaItem.query.filter_by(ativo_id=ativo.id).order_by(PreventivaItem.id).all()

    data = []
    for it in itens:
        data.append(
            {
                "id": it.id,
                "nome": it.nome,
                "base": it.base,
                "intervalo": it.intervalo,
                "primeira_execucao": it.primeira_execucao,
                "avisar_antes": it.avisar_antes,
            }
        )

    return jsonify({"ativo_id": ativo.id, "plano": data})


@api_ativos_bp.post("/<int:id>/plano")
def criar_item_plano(id):
    """
    Cria um item de plano para o ativo.
    Espera JSON:

    {
      "nome": "Troca de óleo",
      "base": "horas" ou "dias",
      "intervalo": 100,
      "primeira_execucao": 50,   (opcional)
      "avisar_antes": 10         (opcional)
    }
    """
    ativo = Ativo.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    nome = (data.get("nome") or "").strip()
    base = (data.get("base") or "horas").lower()
    intervalo = data.get("intervalo")
    primeira = data.get("primeira_execucao")
    avisar = data.get("avisar_antes")

    if not nome:
        return jsonify({"erro": "nome é obrigatório"}), 400

    if base not in ("horas", "dias"):
        return jsonify({"erro": "base deve ser 'horas' ou 'dias'"}), 400

    try:
        intervalo = float(intervalo)
    except (TypeError, ValueError):
        return jsonify({"erro": "intervalo inválido"}), 400

    if intervalo <= 0:
        return jsonify({"erro": "intervalo deve ser > 0"}), 400

    def _to_float_or_none(v):
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    primeira = _to_float_or_none(primeira)
    avisar = _to_float_or_none(avisar)

    it = PreventivaItem(
        ativo_id=ativo.id,
        nome=nome,
        base=base,
        intervalo=intervalo,
        primeira_execucao=primeira,
        avisar_antes=avisar,
    )
    db.session.add(it)
    db.session.commit()

    return jsonify({"mensagem": "item criado com sucesso", "id": it.id}), 201


@api_ativos_bp.delete("/<int:id>/plano/<int:item_id>")
def excluir_item_plano(id, item_id):
    """Exclui um item de plano do ativo."""
    ativo = Ativo.query.get_or_404(id)

    it = PreventivaItem.query.filter_by(ativo_id=ativo.id, id=item_id).first()
    if not it:
        return jsonify({"erro": "item não encontrado"}), 404

    db.session.delete(it)
    db.session.commit()

    return jsonify({"mensagem": "item excluído com sucesso"})
