import time
from flask import jsonify

from gerenciador_ativos.api.ativos import api_ativos_bp
from gerenciador_ativos.models import Ativo

# Regras fixas de manutenção (horas de motor)
# Você pode ajustar esses valores depois com base no manual do motor
MANUTENCAO_REGRAS = [
    {
        "nome": "Troca de óleo do motor",
        "intervalo": 100.0,  # a cada 100 h
    },
    {
        "nome": "Troca do filtro de óleo",
        "intervalo": 200.0,  # a cada 200 h
    },
    {
        "nome": "Drenar separador de água/combustível",
        "intervalo": 50.0,  # a cada 50 h
    },
]


@api_ativos_bp.get("/<int:id>/preventiva")
def preventiva_ativo(id):
    """
    Retorna as próximas atividades de preventiva para o ativo,
    calculadas em função das horas de motor acumuladas.
    Resposta esperada pelo painel V2:

    {
      "tarefas": [
        {"nome": "Troca de óleo...", "faltam": 12.5},
        ...
      ]
    }
    """
    ativo = Ativo.query.get_or_404(id)

    # Horas acumuladas que já salvamos no banco
    horas_total = float(getattr(ativo, "horas_sistema_total", 0.0) or 0.0)

    # Se o motor estiver ligado, soma o ciclo atual (tempo desde que ligou)
    ts_ligado = getattr(ativo, "timestamp_ligado", None)
    if ts_ligado is not None:
        agora_ts = time.time()
        ciclo_h = max(0.0, (agora_ts - float(ts_ligado)) / 3600.0)
        horas_total += ciclo_h

    tarefas = []

    for regra in MANUTENCAO_REGRAS:
        nome = regra["nome"]
        intervalo = float(regra.get("intervalo", 0.0) or 0.0)
        if intervalo <= 0:
            continue

        # quanto já "andou" desde o último múltiplo do intervalo
        resto = horas_total % intervalo
        faltam = intervalo - resto if resto > 0 else intervalo

        tarefas.append(
            {
                "nome": nome,
                "faltam": round(faltam, 1),
            }
        )

    # Ordena pelas que estão mais próximas de vencer
    tarefas.sort(key=lambda t: t["faltam"])

    return jsonify({"tarefas": tarefas})
