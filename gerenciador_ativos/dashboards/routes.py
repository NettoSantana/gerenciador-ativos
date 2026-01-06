from flask import Blueprint, jsonify
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.ativos.utils import calcular_horas_motor

dashboard_api_bp = Blueprint(
    "dashboard_api",
    __name__,
    url_prefix="/api"
)


def _first_attr(obj, names, default="—"):
    """
    Pega o primeiro atributo existente e útil (não None / não vazio).
    """
    for name in names:
        if not hasattr(obj, name):
            continue
        val = getattr(obj, name)
        if val is None:
            continue
        if isinstance(val, str) and not val.strip():
            continue
        return val
    return default


def _fmt_bateria(val):
    if val is None or val == "—":
        return "—"
    try:
        return round(float(val), 1)
    except Exception:
        return val


@dashboard_api_bp.route("/dashboard-geral", methods=["GET"])
def dashboard_geral_api():
    """
    Dashboard Geral (TV)
    Retorna uma lista de linhas para o painel.
    """
    ativos = Ativo.query.filter_by(ativo=True).all()

    dados = []
    for ativo in ativos:
        # Se no futuro você criar colunas reais, isso aqui já passa a preencher automaticamente:
        cotista_dia = _first_attr(ativo, ["cotista_dia", "cotista", "cotista_do_dia"], default="—")
        lavagem = _first_attr(ativo, ["lavagem_interna", "lavagem", "lavagem_ok"], default="—")
        pendencias = _first_attr(ativo, ["pendencias", "pendencia", "obs_pendencias"], default="—")

        horas = "—"
        try:
            horas_calc = calcular_horas_motor(ativo)
            if horas_calc is not None and str(horas_calc).strip() != "":
                horas = horas_calc
        except Exception:
            horas = "—"

        bateria_raw = _first_attr(ativo, ["tensao_bateria", "bateria", "bateria_v", "bateria_volts"], default=None)
        bateria = _fmt_bateria(bateria_raw)

        dados.append({
            "embarcacao": _first_attr(ativo, ["nome", "embarcacao", "descricao"], default="—"),
            "cotista_dia": cotista_dia,
            "horas": horas,
            "lavagem_interna": lavagem,
            "pendencias": pendencias,
            "bateria": bateria,
        })

    return jsonify(dados)
