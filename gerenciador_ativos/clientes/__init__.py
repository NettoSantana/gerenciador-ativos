from flask import Blueprint

clientes_bp = Blueprint(
    "clientes",
    __name__,
    url_prefix="/clientes",
    template_folder="../../templates/clientes"
)

from gerenciador_ativos.clientes import routes  # noqa
