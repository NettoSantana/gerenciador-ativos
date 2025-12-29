from flask import Blueprint, render_template

dashboard_geral_bp = Blueprint(
    "dashboard_geral",
    __name__
)

@dashboard_geral_bp.route("/dashboard-geral")
def dashboard_geral():
    return render_template("dashboards/painel_tv.html")
