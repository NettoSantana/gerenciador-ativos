from flask import Blueprint

usuarios_bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios",
    template_folder="../../templates/usuarios"
)

from gerenciador_ativos.usuarios import routes  # noqa
