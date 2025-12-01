from datetime import datetime
from gerenciador_ativos.extensions import db


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # PF / PJ
    documento = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(50), nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    ativos = db.relationship("Ativo", backref="cliente", lazy=True)

    def __repr__(self):
        return f"<Cliente {self.nome}>"


class Ativo(db.Model):
    __tablename__ = "ativos"

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    imei = db.Column(db.String(50), nullable=True)

    status_monitoramento = db.Column(db.String(50), default="desconhecido")

    # ================================
    # NOVOS CAMPOS — TELEMETRIA V2 PRO
    # ================================

    # Horas de motor (vindas da BrasilSat) + offset manual
    horas_motor = db.Column(db.Float, default=0.0)
    horas_motor_offset = db.Column(db.Float, default=0.0)

    # Horas do sistema — contadas apenas quando motor está LIGADO
    horas_sistema_total = db.Column(db.Float, default=0.0)
    timestamp_ligado = db.Column(db.DateTime, nullable=True)

    # Horas paradas — contagem enquanto motor está DESLIGADO
    timestamp_desligado = db.Column(db.DateTime, nullable=True)

    # Contador de ignições — sempre que ACC passa de 0 → 1
    total_ignicoes = db.Column(db.Integer, default=0)
    acc_anterior = db.Column(db.Integer, default=0)

    # Bateria
    tensao_bateria = db.Column(db.Float, default=0.0)

    # Atualização
    ultima_atualizacao = db.Column(db.DateTime, nullable=True)

    def atualizar_motor(self, acc_atual):
        """Atualiza ignições, horas do sistema e horas paradas com base no status ACC."""

        agora = datetime.utcnow()

        # --------------------------------
        # 1) Contagem de ignições (0 → 1)
        # --------------------------------
        if self.acc_anterior == 0 and acc_atual == 1:
            self.total_ignicoes += 1
            self.timestamp_ligado = agora
            self.timestamp_desligado = None  # resetar horas paradas

        # --------------------------------
        # 2) Motor desligando (1 → 0)
        # --------------------------------
        if self.acc_anterior == 1 and acc_atual == 0:
            if self.timestamp_ligado:
                tempo_ligado = (agora - self.timestamp_ligado).total_seconds() / 3600
                self.horas_sistema_total += max(tempo_ligado, 0)
            self.timestamp_ligado = None
            self.timestamp_desligado = agora  # começa contagem de horas paradas

        # --------------------------------
        # 3) Horas paradas (contador só de exibição)
        # --------------------------------
        # (não fica salvo acumulado — apenas calculado no painel)

        # Atualiza estado anterior
        self.acc_anterior = acc_atual

    def horas_paradas(self):
        """Retorna horas em que o motor está parado (não acumula)."""
        if not self.timestamp_desligado:
            return 0.0

        agora = datetime.utcnow()
        return (agora - self.timestamp_desligado).total_seconds() / 3600

    def estado_motor(self):
        """Retorna texto baseado no ACC."""
        return "ligado" if self.acc_anterior == 1 else "desligado"

    def __repr__(self):
        return f"<Ativo {self.nome}>"


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # admin, gerente, cliente
    ativo = db.Column(db.Boolean, default=True)

    # cliente atrelado (somente para usuários tipo "cliente")
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=True)

    def set_password(self, senha):
        from werkzeug.security import generate_password_hash
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.senha_hash, senha)

    def is_interno(self):
        return self.tipo in ["admin", "gerente"]

    def __repr__(self):
        return f"<Usuario {self.email}>"
