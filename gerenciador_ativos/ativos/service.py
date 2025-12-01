from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo


def criar_ativo(nome, categoria, imei, cliente_id, observacoes=None):
    ativo = Ativo(
        nome=nome,
        categoria=categoria,
        imei=imei or None,
        observacoes=observacoes,
        cliente_id=cliente_id,
        ativo=True
    )

    db.session.add(ativo)
    db.session.commit()
    return ativo


def atualizar_ativo(ativo, nome, categoria, imei, cliente_id, observacoes=None):
    ativo.nome = nome
    ativo.categoria = categoria
    ativo.imei = imei or None
    ativo.observacoes = observacoes
    ativo.cliente_id = cliente_id

    db.session.commit()
    return ativo


def excluir_ativo(ativo):
    db.session.delete(ativo)
    db.session.commit()
