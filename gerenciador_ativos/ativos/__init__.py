from flask import Blueprint

ativos_bp = Blueprint(
    "ativos",
    __name__,
    url_prefix="/ativos",
    template_folder="../../templates/ativos"
)

from gerenciador_ativos.ativos import routes  # noqa
