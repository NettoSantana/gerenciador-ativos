from flask import Blueprint

# Blueprint principal da API de ativos
api_ativos_bp = Blueprint("api_ativos", __name__, url_prefix="/api/ativos")

# Importa módulos de rotas (mantém aqui para registrar no blueprint)
from . import dados  # noqa
from . import preventiva  # noqa
