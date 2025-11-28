from flask import Blueprint, render_template, g, abort
from gerenciador_ativos.auth.decorators import login_required, role_required
from gerenciador_ativos.models import Ativo, Cliente

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")


@portal_bp.route("/dashboard")
@login_required
@role_required(["cliente"])
def dashboard_cliente():
    """
    Painel do Cliente:
    - Mostra dados do cliente vinculado ao usuário logado
    - Lista apenas os ativos desse cliente
    """
    usuario = getattr(g, "user", None)

    if not usuario:
        abort(401)

    if not usuario.cliente_id:
        # Usuário tipo cliente SEM cliente vinculado → não deveria acontecer
        abort(403)

    cliente = Cliente.query.get_or_404(usuario.cliente_id)

    ativos = (
        Ativo.query
        .filter_by(cliente_id=cliente.id)
        .order_by(Ativo.nome)
        .all()
    )

    qtd_ativos = len(ativos)

    return render_template(
        "portal/dashboard_cliente.html",
        cliente=cliente,
        ativos=ativos,
        qtd_ativos=qtd_ativos,
    )
