import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request
from gerenciador_ativos.models import Ativo

dashboard_api_bp = Blueprint(
    "dashboard_api",
    __name__,
    url_prefix="/api"
)


def _get_db_path():
    instance_path = os.environ.get("INSTANCE_PATH", "/app/instance")
    return os.path.join(instance_path, "gerenciador_ativos.db")


def _get_local_day_iso():
    """
    Retorna YYYY-MM-DD baseado no timezone do Brasil (configurável via env TZ).
    Default: America/Bahia
    """
    tz_name = os.environ.get("TZ", "America/Bahia")
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("America/Bahia")
    return datetime.now(tz).date().isoformat()


def _carregar_cotistas_do_dia(dia_iso: str):
    """
    Retorna dict: { ativo_id: cotista }
    """
    db_path = _get_db_path()
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT ativo_id, cotista
        FROM cotista_dia
        WHERE data = ?;
    """, (dia_iso,))

    rows = cur.fetchall()
    conn.close()

    cotistas = {}
    for ativo_id, cotista in rows:
        cotistas[int(ativo_id)] = cotista

    return cotistas


@dashboard_api_bp.route("/dashboard-geral", methods=["GET"])
def dashboard_geral_api():
    """
    Endpoint dedicado para o Dashboard Geral (TV).

    Inclui:
    - cotista_dia (por ativo e por data)

    Regras:
    - Usa data local (TZ Brasil) por padrão
    - Permite override via querystring: ?data=YYYY-MM-DD
    """

    dia = (request.args.get("data") or "").strip()
    if not dia:
        dia = _get_local_day_iso()

    cotistas = _carregar_cotistas_do_dia(dia)

    ativos = Ativo.query.filter_by(ativo=True).all()

    dados = []
    for ativo in ativos:
        dados.append({
            "embarcacao": ativo.nome,
            "cotista_dia": cotistas.get(ativo.id, "—"),
            "horas": getattr(ativo, "horas_uso", "—"),
            "lavagem_interna": "—",
            "pendencias": "—",
            "bateria": getattr(ativo, "tensao_bateria", "—")
        })

    return jsonify(dados)
