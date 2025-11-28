from typing import Optional
from gerenciador_ativos.models import Usuario


def autenticar_usuario(email: str, senha: str) -> Optional[Usuario]:
    """Retorna o usuário se login OK, senão None."""
    email = (email or "").strip().lower()
    if not email or not senha:
        return None

    usuario = Usuario.query.filter_by(email=email, ativo=True).first()
    if not usuario:
        return None

    if not usuario.check_password(senha):
        return None

    return usuario
