from flask import render_template
from gerenciador_ativos.dashboards import dashboards_bp
from gerenciador_ativos.auth.decorators import login_required
from gerenciador_ativos.models import Cliente, Ativo
from gerenciador_ativos.preventiva_models import PreventivaItem


@dashboards_bp.route("/dashboard/gerente")
@login_required
def dashboard_gerente():

    # =======================
    # CONTAGENS DO SISTEMA
    # =======================
    total_clientes = Cliente.query.count()
    total_ativos = Ativo.query.count()
    total_ativos_ativos = Ativo.query.filter_by(ativo=True).count()

    # conta itens de preventiva cadastrados
    total_preventivas = PreventivaItem.query.count()

    # =======================
    # Renderiza com dados reais
    # =======================
    return render_template(
        "dashboards/gerente.html",
        total_clientes=total_clientes,
        total_ativos=total_ativos,
        total_ativos_ativos=total_ativos_ativos,
        total_preventivas=total_preventivas
    )
