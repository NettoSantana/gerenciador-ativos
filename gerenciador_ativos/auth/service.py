from gerenciador_ativos.extensions import db
from gerenciador_ativos.usuarios.models import Usuario


def autenticar_usuario(email, senha):
    """
    Autentica usuário pelo email e senha.
    Retorna o usuário se válido, senão None.
    """

    usuario = Usuario.query.filter_by(email=email, ativo=True).first()

    if not usuario:
        return None

    if not usuario.check_password(senha):
        return None

    return usuario
