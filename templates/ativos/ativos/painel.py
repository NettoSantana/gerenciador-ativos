from flask import Blueprint, render_template
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.auth.decorators import login_required

painel_bp = Blueprint("painel_ativos", __name__, url_prefix="/painel-ativo")

@painel_bp.route("/<int:id>")
@login_required
def painel(id):
    ativo = Ativo.query.get_or_404(id)
    return render_template("ativos/painel.html", ativo=ativo)
