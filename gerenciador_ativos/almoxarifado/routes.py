from flask import Blueprint, render_template
from gerenciador_ativos.auth.decorators import login_required, gerente_required
from gerenciador_ativos.models import AlmoxItem

almoxarifado_bp = Blueprint(
    "almoxarifado",
    __name__,
    url_prefix="/almoxarifado"
)


# ============================================================
# LISTAGEM DE ITENS
# ============================================================
@almoxarifado_bp.route("/")
@login_required
@gerente_required
def lista():
    itens = (
        AlmoxItem.query
        .filter_by(ativo=True)
        .order_by(AlmoxItem.nome)
        .all()
    )

    return render_template(
        "almoxarifado/index.html",
        itens=itens
    )
