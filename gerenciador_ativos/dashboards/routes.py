from flask import render_template, session, redirect, url_for
from gerenciador_ativos.dashboards import dashboards_bp
from gerenciador_ativos.auth.decorators import login_required


@dashboards_bp.route("/")
def home():
    # se estiver logado, manda pro dashboard correto
    if "user_id" in session:
        if session.get("user_tipo") in ["admin", "gerente", "manutencao", "financeiro", "fiscal"]:
            return redirect(url_for("dashboards.dashboard_gerente"))
        else:
            return redirect(url_for("dashboards.dashboard_cliente"))
    # senão, manda pro login
    return redirect(url_for("auth.login"))


@dashboards_bp.route("/dashboard/gerente")
@login_required
def dashboard_gerente():
    return render_template("dashboards/gerente.html")


@dashboards_bp.route("/dashboard/cliente")
@login_required
def dashboard_cliente():
    return render_template("dashboards/cliente.html")
