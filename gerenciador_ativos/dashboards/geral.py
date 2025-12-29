from flask import Blueprint, render_template

dashboard_geral_bp = Blueprint(
    "dashboard_geral",
    __name__,
    template_folder="templates"
)

@dashboard_geral_bp.route("/dashboard-geral")
def dashboard_geral():
    return render_template("painel_tv.html")
