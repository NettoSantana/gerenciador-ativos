from flask import Blueprint, render_template, abort, session
from gerenciador_ativos.auth.decorators import login_required
from gerenciador_ativos.models import Ativo, Cliente, Usuario

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")


def _get_usuario_cliente():
    """
    Carrega o usuário logado a partir da sessão
    e garante que ele é do tipo 'cliente' e tem cliente_id vinculado.
    """
    user_id = session.get("user_id")
    user_tipo = session.get("user_tipo")

    if not user_id:
        abort(401)

    if user_tipo != "cliente":
        abort(403)

    usuario = Usuario.query.get(user_id)
    if not usuario:
        abort(401)

    if not usuario.cliente_id:
        abort(403)

    return usuario


@portal_bp.route("/dashboard")
@login_required
def dashboard_cliente():
    """
    Painel do Cliente:
    - Mostra dados do cliente vinculado ao usuário logado
    - Lista apenas os ativos desse cliente
    """
    usuario = _get_usuario_cliente()

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


@portal_bp.route("/ativo/<int:ativo_id>")
@login_required
def painel_ativo_cliente(ativo_id: int):
    """
    Painel completo de um ativo específico para o cliente.

    - Garante que o ativo pertence ao cliente logado
    - Renderiza o template com os cards de monitoramento (versão 2)
    """
    usuario = _get_usuario_cliente()

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
