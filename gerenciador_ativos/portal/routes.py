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


# ---------------------------------------------------
# NOVO: Painel de um ativo específico para o CLIENTE
# ---------------------------------------------------
@portal_bp.route("/ativo/<int:ativo_id>")
@login_required
@role_required(["cliente"])
def painel_ativo_cliente(ativo_id: int):
    """
    Painel completo de um ativo específico para o cliente.

    - Garante que o ativo pertence ao cliente logado
    - Renderiza o template com os cards de monitoramento (versão 2)
    """
    usuario = getattr(g, "user", None)
    if not usuario or not usuario.cliente_id:
        abort(403)

    # Busca o ativo
    ativo = Ativo.query.get_or_404(ativo_id)

    # Garante que o ativo é do cliente logado
    if ativo.cliente_id != usuario.cliente_id:
        abort(403)

    cliente = Cliente.query.get_or_404(usuario.cliente_id)

    return render_template(
        "portal/ativo_painel.html",
        cliente=cliente,
        ativo=ativo,
    )
