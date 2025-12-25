from datetime import date, datetime
from gerenciador_ativos.extensions import db


class ConsumoDiario(db.Model):
    __tablename__ = "consumo_diario"

    id = db.Column(db.Integer, primary_key=True)

    ativo_id = db.Column(
        db.Integer,
        db.ForeignKey("ativos.id"),
        nullable=False,
        index=True
    )

    data = db.Column(db.Date, nullable=False, index=True)

    horas_motor_dia = db.Column(db.Float, nullable=False, default=0.0)

    consumo_estimado_dia = db.Column(db.Float, nullable=False, default=0.0)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("ativo_id", "data", name="uix_ativo_data"),
    )

    def __repr__(self):
        return (
            f"<ConsumoDiario ativo_id={self.ativo_id} "
            f"data={self.data} consumo={self.consumo_estimado_dia}>"
        )
