from flask import Blueprint

# Blueprint principal da API de ativos
api_ativos_bp = Blueprint("api_ativos", __name__, url_prefix="/api/ativos")

# Importa os módulos internos (rotas do REST)
from . import dados  # noqa
