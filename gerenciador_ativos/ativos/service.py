from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo


# --------------------------------------------------------
# CRIAR ATIVO
# --------------------------------------------------------
def criar_ativo(cliente_id, nome, categoria, imei, observacoes):
    ativo = Ativo(
        cliente_id=cliente_id,
        nome=nome,
        categoria=categoria or None,
        imei=imei or None,
        observacoes=observacoes or None,
        ativo=True
    )

    db.session.add(ativo)
    db.session.commit()
    return ativo


# --------------------------------------------------------
# ATUALIZAR ATIVO
# --------------------------------------------------------
def atualizar_ativo(ativo_id, cliente_id, nome, categoria, imei, observacoes):
    ativo = Ativo.query.get_or_404(ativo_id)

    ativo.cliente_id = cliente_id
    ativo.nome = nome
    ativo.categoria = categoria or None
    ativo.imei = imei or None
    ativo.observacoes = observacoes or None

    db.session.commit()
    return ativo


# --------------------------------------------------------
# EXCLUIR ATIVO (nome correto para a rota)
# --------------------------------------------------------
def excluir_ativo(ativo_id):
    ativo = Ativo.query.get_or_404(ativo_id)
    db.session.delete(ativo)
    db.session.commit()
