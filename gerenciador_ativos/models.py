from datetime import datetime
from gerenciador_ativos.extensions import db


# =====================================================================
#  CLIENTE  (AGORA VERSÃO COMPLETA: documento + endereco + observacoes)
# =====================================================================
class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # PF / PJ

    # CPF ou CNPJ
    documento = db.Column(db.String(50), nullable=True)

    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(50), nullable=True)

    # NOVOS CAMPOS (compatível com telas e service)
    endereco = db.Column(db.String(255), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    ativo = db.Column(db.Boolean, default=True)

    ativos = db.relationship("Ativo", backref="cliente", lazy=True)

    def __repr__(self):
        return f"<Cliente {self.nome}>"


# =====================================================================
#  ATIVO — TELEMETRIA V2 COMPLETA
# =====================================================================
class Ativo(db.Model):
    __tablename__ = "ativos"

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    imei = db.Column(db.String(50), nullable=True)

    status_monitoramento = db.Column(db.String(50), default="desconhecido")

    # --------------------------
    # TELEMETRIA V2 PRO
    # --------------------------

    horas_motor = db.Column(db.Float, default=0.0)
    horas_motor_offset = db.Column(db.Float, default=0.0)

    horas_sistema_total = db.Column(db.Float, default=0.0)
    timestamp_ligado = db.Column(db.DateTime, nullable=True)

    timestamp_desligado = db.Column(db.DateTime, nullable=True)

    total_ignicoes = db.Column(db.Integer, default=0)
    acc_anterior = db.Column(db.Integer, default=0)

    tensao_bateria = db.Column(db.Float, default=0.0)

    ultima_atualizacao = db.Column(db.DateTime, nullable=True)

    # --------------------------
    # MÉTODOS DE PROCESSAMENTO
    # --------------------------

    def atualizar_motor(self, acc_atual):
        agora = datetime.utcnow()

        # ignição detectada (0 → 1)
        if self.acc_anterior == 0 and acc_atual == 1:
            self.total_ignicoes += 1
            self.timestamp_ligado = agora
            self.timestamp_desligado = None

        # desligamento detectado (1 → 0)
        if self.acc_anterior == 1 and acc_atual == 0:
            if self.timestamp_ligado:
                tempo_ligado = (agora - self.timestamp_ligado).total_seconds() / 3600
                self.horas_sistema_total += max(tempo_ligado, 0)
            self.timestamp_ligado = None
            self.timestamp_desligado = agora

        self.acc_anterior = acc_atual

    def horas_paradas(self):
        if not self.timestamp_desligado:
            return 0.0
        agora = datetime.utcnow()
        return (agora - self.timestamp_desligado).total_seconds() / 3600

    def estado_motor(self):
        return "ligado" if self.acc_anterior == 1 else "desligado"

    def __repr__(self):
        return f"<Ativo {self.nome}>"


# =====================================================================
#  USUÁRIO
# =====================================================================
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # admin, gerente, cliente
    ativo = db.Column(db.Boolean, default=True)

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
