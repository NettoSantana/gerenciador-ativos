from datetime import datetime, timezone

from flask import Blueprint, jsonify

from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo
from gerenciador_ativos.api.monitoramento.brasilsat import (
    get_telemetria_por_imei,
    BrasilSatError,
)

monitoramento_bp = Blueprint("monitoramento", __name__, url_prefix="/api")


def _dt_from_ts(ts: float) -> datetime:
    """Converte timestamp (segundos) para datetime UTC seguro."""
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except Exception:
        return datetime.now(tz=timezone.utc)


@monitoramento_bp.get("/ativos/<int:ativo_id>/dados")
def api_ativo_dados(ativo_id: int):
    """Dados em tempo real do ativo (para o painel)."""
    ativo = Ativo.query.get_or_404(ativo_id)

    if not ativo.imei:
        return jsonify({"erro": "Ativo sem IMEI configurado."}), 400

    # 1) Busca telemetria na BrasilSat
    try:
        telem = get_telemetria_por_imei(ativo.imei)
    except BrasilSatError as exc:
        return jsonify({"erro": str(exc)}), 502

    # --- Campos básicos vindos da BrasilSat ---
    servertime = telem.get("servertime") or telem.get("server_time")
    if not servertime:
        agora = datetime.now(tz=timezone.utc)
        servertime = int(agora.timestamp())
    dt_atual = _dt_from_ts(servertime)

    motor_ligado_atual = bool(telem.get("engine_on") or telem.get("acc_on"))

    # 2) Acúmulo de horas de sistema e horas paradas
    delta_horas = 0.0
    if ativo.ultima_atualizacao:
        dt_ant = ativo.ultima_atualizacao
        if dt_ant.tzinfo is None:
            dt_ant = dt_ant.replace(tzinfo=timezone.utc)

        delta_horas = (dt_atual - dt_ant).total_seconds() / 3600.0

        # Proteção contra buracos gigantes (ex.: dias sem comunicar)
        if 0 < delta_horas < 24:
            if ativo.ultimo_estado_motor:
                # Motor ficou LIGADO nesse intervalo
                ativo.horas_sistema = (ativo.horas_sistema or 0.0) + delta_horas
            else:
                # Motor ficou DESLIGADO nesse intervalo
                ativo.horas_paradas = (ativo.horas_paradas or 0.0) + delta_horas

    # 3) Contagem de ignições (transição OFF -> ON)
    prev_motor_on = bool(ativo.ultimo_estado_motor)
    if not prev_motor_on and motor_ligado_atual:
        ativo.total_ignicoes = (ativo.total_ignicoes or 0) + 1

    # 4) Atualiza estado persistido do ativo
    ativo.ultima_atualizacao = dt_atual
    ativo.ultimo_estado_motor = motor_ligado_atual
    db.session.commit()

    # 5) Horas de motor vindas da BrasilSat (acctime em segundos)
    acctime_s = (
        telem.get("acctime_s")
        or telem.get("engine_on_time_s")
        or telem.get("engine_hours_s")
        or 0
    )
    try:
        horas_motor = float(acctime_s) / 3600.0
    except Exception:
        horas_motor = 0.0

    # 6) NOVO — Hora da embarcação
    horas_offset = float(ativo.horas_offset or 0.0)
    horas_sistema = float(ativo.horas_sistema or 0.0)
    hora_embarcacao = horas_offset + horas_sistema

    # 7) Monta resposta para o painel
    resp = {
        "imei": ativo.imei,
        "servertime": servertime,
        "monitor_online": bool(telem.get("online", True)),
        "motor_ligado": motor_ligado_atual,
        "tensao_bateria": telem.get("battery_volt")
        or telem.get("ext_battery_volt")
        or 0.0,
        "latitude": telem.get("lat"),
        "longitude": telem.get("lng"),

        # Horas vindas do sistema
        "horas_motor": round(horas_motor, 2),

        # Horas acumuladas pelo backend
        "horas_paradas": round(ativo.horas_paradas or 0.0, 2),
        "horas_sistema": round(horas_sistema, 2),

        # NOVO — campos reais
        "horas_offset": round(horas_offset, 2),
        "hora_embarcacao": round(hora_embarcacao, 2),

        # ignições
        "ignicoes": int(ativo.total_ignicoes or 0),
    }

    return jsonify(resp)
