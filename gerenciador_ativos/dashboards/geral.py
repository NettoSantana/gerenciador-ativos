from flask import Blueprint, render_template, session, redirect, url_for
from flask_login import login_required
from sqlalchemy import text

from gerenciador_ativos.extensions import db

dashboard_geral_bp = Blueprint("dashboard_geral", __name__)


def _table_exists(table_name: str) -> bool:
    row = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": table_name},
    ).fetchone()
    return row is not None


def _safe_count(table_name: str) -> int:
    try:
        if not _table_exists(table_name):
            return 0
        return int(db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() or 0)
    except Exception:
        return 0


def _safe_count_preventivas() -> int:
    """
    Tenta achar uma tabela de preventivas (nome pode variar).
    Prioriza 'preventivas' se existir. Senão pega a primeira que contenha 'prevent'.
    """
    try:
        rows = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE :p"),
            {"p": "%prevent%"},
        ).fetchall()

        if not rows:
            return 0

        names = [r[0] for r in rows if r and r[0]]
        if not names:
            return 0

        table = "preventivas" if "preventivas" in names else names[0]
        return int(db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0)
    except Exception:
        return 0


def _require_admin_or_gerente():
    tipo = session.get("user_tipo")
    if tipo not in ["admin", "gerente"]:
        return redirect(url_for("portal.dashboard_cliente"))
    return None


# ==============================
# HOME DO ADMIN/GERENTE
# ==============================
@dashboard_geral_bp.route("/dashboard-geral")
@login_required
def dashboard_geral():
    guard = _require_admin_or_gerente()
    if guard:
        return guard

    total_clientes = _safe_count("clientes")
    total_ativos_ativos = _safe_count("ativos")
    total_preventivas = _safe_count_preventivas()

    return render_template(
        "dashboards/gerente.html",
        total_clientes=total_clientes,
        total_ativos_ativos=total_ativos_ativos,
        total_preventivas=total_preventivas,
    )


# ==============================
# ROTA ANTIGA (NÃO QUEBRA)
# ==============================
@dashboard_geral_bp.route("/dashboard/gerente")
@login_required
def dashboard_gerente():
    # Mantém compatibilidade: qualquer lugar que ainda use /dashboard/gerente
    # vai cair no HOME oficial (/dashboard-geral)
    return redirect("/dashboard-geral")


# ==============================
# TELA TV (PÚBLICA)
# ==============================
@dashboard_geral_bp.route("/tv")
def dashboard_tv():
    return render_template("ativos/painel_tv.html")
