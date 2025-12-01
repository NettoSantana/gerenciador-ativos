from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario


def criar_usuario(nome, email, senha, tipo, cliente_id=None):
    usuario = Usuario(
        nome=nome,
        email=email.lower(),
        tipo=tipo,
        cliente_id=cliente_id,
        ativo=True
    )
    usuario.set_senha(senha)  # <-- CORRETO AGORA
    db.session.add(usuario)
    db.session.commit()
    return usuario


def atualizar_usuario(usuario, nome, email, tipo, cliente_id):
    usuario.nome = nome
    usuario.email = email.lower()
    usuario.tipo = tipo
    usuario.cliente_id = cliente_id
    db.session.commit()
    return usuario


def desativar_usuario(usuario):
    usuario.ativo = False
    db.session.commit()


def ativar_usuario(usuario):
    usuario.ativo = True
    db.session.commit()
