from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo


def criar_ativo(cliente_id, nome, categoria, tipo, modelo,
                numero_serie, codigo_interno, localizacao,
                status_operacional, observacoes):
    ativo = Ativo(
        cliente_id=cliente_id,
        nome=nome,
        categoria=categoria,
        tipo=tipo,
        modelo=modelo,
        numero_serie=numero_serie,
        codigo_interno=codigo_interno,
        localizacao=localizacao,
        status_operacional=status_operacional,
        observacoes=observacoes,
        ativo=True
    )
    db.session.add(ativo)
    db.session.commit()
    return ativo


def atualizar_ativo(ativo, cliente_id, nome, categoria, tipo, modelo,
                    numero_serie, codigo_interno, localizacao,
                    status_operacional, observacoes):
    ativo.cliente_id = cliente_id
    ativo.nome = nome
    ativo.categoria = categoria
    ativo.tipo = tipo
    ativo.modelo = modelo
    ativo.numero_serie = numero_serie
    ativo.codigo_interno = codigo_interno
    ativo.localizacao = localizacao
    ativo.status_operacional = status_operacional
    ativo.observacoes = observacoes
    db.session.commit()
    return ativo


def desativar_ativo(ativo):
    ativo.ativo = False
    db.session.commit()


def ativar_ativo(ativo):
    ativo.ativo = True
    db.session.commit()
