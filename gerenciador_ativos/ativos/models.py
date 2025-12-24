from datetime import datetime
from gerenciador_ativos.extensions import db


class Ativo(db.Model):
    __tablename__ = "ativos"

    id = db.Column(db.Integer, primary_key=True)

    # Identificação
    nome = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # jet | lancha
    imei = db.Column(db.String(50), unique=True, nullable=True)

    # Horas
    horas_motor = db.Column(db.Float, default=0)       # horas reais vindas do rastreador
    horas_offset = db.Column(db.Float, default=0)      # ajuste manual
    horas_total = db.Column(db.Float, default=0)       # horas_motor + horas_offset

    # 🔥 CONSUMO MÉDIO ESTIMADO (L/h)
    consumo_litros_hora = db.Column(db.Float, default=0)

    # Status
    ativo = db.Column(db.Boolean, default=True)

    # Auditoria
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ------------------------------------------------------------------
    # MÉTODOS
    # ------------------------------------------------------------------

    def recalcular_horas(self):
        """
        Recalcula as horas totais da embarcação.
        """
        self.horas_total = (self.horas_motor or 0) + (self.horas_offset or 0)

    def consumo_estimado(self):
        """
        Retorna o consumo total estimado com base nas horas de motor.
        """
        if not self.consumo_litros_hora or not self.horas_motor:
            return 0
        return round(self.horas_motor * self.consumo_litros_hora, 2)

    def consumo_medio(self):
        """
        Retorna o consumo médio estimado (L/h).
        """
        return round(self.consumo_litros_hora or 0, 2)
