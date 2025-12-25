from gerenciador_ativos.usuarios.service import Usuario


def autenticar_usuario(email, senha):
    usuario = Usuario.query.filter_by(email=email, ativo=True).first()

    if not usuario:
        return None

    if not usuario.check_password(senha):
        return None

    return usuario
