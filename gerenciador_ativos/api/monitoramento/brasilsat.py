def _normalizar_track_bruto(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza o registro bruto em um dicionário mais amigável
    para o restante do sistema.

    Agora inclui também latitude, longitude, velocidade e curso
    (quando disponíveis na BrasilSat).
    """

    imei = record.get("imei")

    # ---- STATUS MOTOR ----
    accstatus = record.get("accstatus")         # 0/1
    acctime_s = record.get("acctime", 0)        # seg com ignição ligada
    externalpower_v = record.get("externalpower")
    servertime = record.get("servertime")

    # ---- LOCALIZAÇÃO ----
    lat = record.get("latitude") or record.get("lat") or None
    lon = record.get("longitude") or record.get("lng") or record.get("lon") or None

    speed = record.get("speed") or record.get("gps_speed") or None
    course = record.get("course") or record.get("direction") or None

    # Conversões
    try:
        acctime_s = float(acctime_s)
    except:
        acctime_s = 0.0

    horas_motor = acctime_s / 3600.0

    try:
        tensao_bateria = float(externalpower_v) if externalpower_v is not None else None
    except:
        tensao_bateria = None

    motor_ligado = bool(accstatus == 1)

    # Latitude / Longitude
    try:
        lat = float(lat) if lat is not None else None
    except:
        lat = None

    try:
        lon = float(lon) if lon is not None else None
    except:
        lon = None

    # Velocidade
    try:
        speed = float(speed) if speed is not None else None
    except:
        speed = None

    return {
        "imei": imei,
        "motor_ligado": motor_ligado,

        "acctime_s": acctime_s,
        "horas_motor": horas_motor,

        "tensao_bateria": tensao_bateria,
        "servertime": servertime,

        # ---- CAMPOS NOVOS ----
        "latitude": lat,
        "longitude": lon,
        "velocidade": speed,
        "direcao": course,

        "raw": record,
    }
