from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Cliente


def criar_cliente(tipo, nome, cpf_cnpj, telefone, email, endereco, observacoes):
    cliente = Cliente(
        tipo=tipo,
        nome=nome,
        cpf_cnpj=cpf_cnpj,
        telefone=telefone,
        email=email,
        endereco=endereco,
        observacoes=observacoes,
        ativo=True
    )
    db.session.add(cliente)
    db.session.commit()
    return cliente


def atualizar_cliente(cliente, tipo, nome, cpf_cnpj, telefone, email, endereco, observacoes):
    cliente.tipo = tipo
    cliente.nome = nome
    cliente.cpf_cnpj = cpf_cnpj
    cliente.telefone = telefone
    cliente.email = email
    cliente.endereco = endereco
    cliente.observacoes = observacoes
    db.session.commit()
    return cliente


def desativar_cliente(cliente):
    cliente.ativo = False
    db.session.commit()


def ativar_cliente(cliente):
    cliente.ativo = True
    db.session.commit()
