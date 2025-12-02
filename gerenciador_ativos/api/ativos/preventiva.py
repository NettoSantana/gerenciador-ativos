import time
from flask import jsonify

from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.preventiva_models import PreventivaItem

# Regras padrão (fallback) caso o ativo não tenha plano cadastrado
FALLBACK_REGRAS = [
    {"nome": "Drenar separador de água/combustível", "intervalo": 50.0, "base": "horas"},
    {"nome": "Troca de óleo do motor", "intervalo": 100.0, "base": "horas"},
    {"nome": "Troca do filtro de óleo", "intervalo": 200.0, "base": "horas"},
]


def _horas_totais_ativo(ativo: Ativo) -> float:
    """Horas totais atuais (acumulado + ciclo ligado)."""
    horas_total = float(getattr(ativo, "horas_sistema_total", 0.0) or 0.0)
    ts_ligado = getattr(ativo, "timestamp_ligado", None)

    if ts_ligado is not None:
        agora_ts = time.time()
        ciclo_h = max(0.0, (agora_ts - float(ts_ligado)) / 3600.0)
        horas_total += ciclo_h

    return horas_total


def _dias_totais_ativo(ativo: Ativo) -> float:
    """
    Dias de uso do ativo.
    Se tiver um campo de data (ex: data_cadastro), usamos ele.
    Senão, cai pra zero e o plano por dias só não anda.
    """
    # tenta usar algum campo de data se existir
    data_ref = getattr(ativo, "data_cadastro", None) or getattr(ativo, "criado_em", None)

    if not data_ref:
        return 0.0

    try:
        ts_ref = data_ref.timestamp()
    except Exception:
        return 0.0

    dias = max(0.0, (time.time() - ts_ref) / 86400.0)
    return dias


@api_ativos_bp.get("/<int:id>/preventiva")
def preventiva_ativo(id):
    """
    Retorna as próximas atividades de preventiva do ativo, usando:

    - plano cadastrado em banco (PreventivaItem), se existir
    - ou regras padrão (fallback) se não houver plano
    """
    ativo = Ativo.query.get_or_404(id)

    horas_total = _horas_totais_ativo(ativo)
    dias_total = _dias_totais_ativo(ativo)

    itens = PreventivaItem.query.filter_by(ativo_id=ativo.id).all()

    tarefas = []

    if itens:
        # Usa plano cadastrado
        for it in itens:
            base = (it.base or "horas").lower()
            intervalo = float(it.intervalo or 0.0)
            primeira = float(it.primeira_execucao or 0.0)

            if intervalo <= 0:
                continue

            if base == "dias":
                medicao = dias_total
            else:
                base = "horas"
                medicao = horas_total

            if medicao < primeira:
                faltam = primeira - medicao
            else:
                med_eff = max(0.0, medicao - primeira)
                resto = med_eff % intervalo
                faltam = intervalo - resto if resto > 0 else intervalo

            tarefas.append(
                {
                    "id": it.id,
                    "nome": it.nome,
                    "base": base,
                    "faltam": round(faltam, 1),
                }
            )
    else:
        # Fallback simples (igual ao que já estava)
        for regra in FALLBACK_REGRAS:
            base = regra.get("base", "horas").lower()
            intervalo = float(regra.get("intervalo", 0.0) or 0.0)
            if intervalo <= 0:
                continue

            medicao = horas_total if base == "horas" else dias_total
            resto = medicao % intervalo
            faltam = intervalo - resto if resto > 0 else intervalo

            tarefas.append(
                {
                    "id": None,
                    "nome": regra["nome"],
                    "base": base,
                    "faltam": round(faltam, 1),
                }
            )

    tarefas.sort(key=lambda t: t["faltam"])

    return jsonify({"tarefas": tarefas})
