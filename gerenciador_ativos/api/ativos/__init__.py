from flask import Blueprint

# Blueprint principal da API de ativos
api_ativos_bp = Blueprint("api_ativos", __name__, url_prefix="/api/ativos")

# Importa todos os módulos de rotas para registrar as URLs
from . import dados       # noqa
from . import preventiva  # noqa
from . import plano       # noqa
from . import offset      # noqa  # <= ROTAS DE AJUSTE DE HORÍMETRO
