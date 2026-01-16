import os
import sqlite3
from datetime import date

from flask import Blueprint, jsonify
from gerenciador_ativos.models import Ativo

dashboard_api_bp = Blueprint(
    "dashboard_api",
    __name__,
    url_prefix="/api"
)


def _get_db_path():
    # padrão Railway / produção
    instance_path = os.environ.get("INSTANCE_PATH", "/app/instance")
    return os.path.join(instance_path, "gerenciador_ativos.db")


def _carregar_cotistas_do_dia(dia_iso: str):
    """
    Retorna dict: { ativo_id: cotista }
    """
    db_path = _get_db_path()
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # tabela criada no ensure_sqlite_schema() do server.py
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

    Agora inclui:
    - cotista_dia: vindo da tabela operacional cotista_dia (por ativo e por data)
    """

    dia = date.today().isoformat()
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
