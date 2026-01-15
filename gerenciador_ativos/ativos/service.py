from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo


def criar_ativo(
    nome,
    categoria,
    cliente_id,
    imei=None,
    tracker_id=None,
    tracking_provider="mobiltracker",
    observacoes=None
):
    ativo = Ativo(
        nome=nome,
        categoria=categoria,
        cliente_id=cliente_id,

        # identificadores de rastreamento
        imei=imei or None,
        tracker_id=tracker_id or None,
        tracking_provider=tracking_provider,

        observacoes=observacoes,
        ativo=True
    )

    db.session.add(ativo)
    db.session.commit()
    return ativo


def atualizar_ativo(
    ativo,
    nome,
    categoria,
    cliente_id,
    imei=None,
    tracker_id=None,
    tracking_provider="mobiltracker",
    observacoes=None
):
    ativo.nome = nome
    ativo.categoria = categoria
    ativo.cliente_id = cliente_id

    # identificadores de rastreamento
    ativo.imei = imei or None
    ativo.tracker_id = tracker_id or None
    ativo.tracking_provider = tracking_provider

    ativo.observacoes = observacoes

    db.session.commit()
    return ativo


def excluir_ativo(ativo):
    db.session.delete(ativo)
    db.session.commit()
