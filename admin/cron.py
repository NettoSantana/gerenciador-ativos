from flask import Blueprint, jsonify
from datetime import date
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo, ConsumoDiario

cron_bp = Blueprint("cron", __name__, url_prefix="/admin/cron")


@cron_bp.route("/fechamento-diario")
def fechamento_diario():
    hoje = date.today()

    ativos = Ativo.query.filter_by(ativo=True).all()

    for ativo in ativos:
        horas_motor = (ativo.horas_offset or 0) + (ativo.horas_sistema or 0)
        consumo_lph = ativo.consumo_lph or 0
        consumo_total = horas_motor * consumo_lph

        existe = ConsumoDiario.query.filter_by(
            ativo_id=ativo.id,
            data_referencia=hoje
        ).first()

        if existe:
            continue

        registro = ConsumoDiario(
            ativo_id=ativo.id,
            data_referencia=hoje,
            horas_motor=horas_motor,
            consumo_lph=consumo_lph,
            consumo_total=consumo_total
        )

        db.session.add(registro)

    db.session.commit()
    return jsonify({"status": "ok", "registros": len(ativos)})
