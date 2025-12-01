from gerenciador_ativos.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# --------------------------------------------------------
# USUÁRIO DO SISTEMA
# admin / gerente / cliente
# --------------------------------------------------------
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)

    tipo = db.Column(db.String(50), default="gerente")
    ativo = db.Column(db.Boolean, default=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=True)

    # --------------------------
    # Métodos de senha corretos
    # --------------------------
    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

    # --------------------------
    # Auxiliar
    # --------------------------
    def is_interno(self):
        return self.tipo in ["admin", "gerente"]

    def __repr__(self):
        return f"<Usuario {self.email}>"


# --------------------------------------------------------
# CLIENTES (PF / PJ)
# --------------------------------------------------------
class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)

    tipo = db.Column(db.String(50), nullable=False)  # PF ou PJ
    nome = db.Column(db.String(120), nullable=False)
    cpf_cnpj = db.Column(db.String(30), nullable=True)
    telefone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    endereco = db.Column(db.String(255), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    ativo = db.Column(db.Boolean, default=True)

    usuarios = db.relationship("Usuario", backref="cliente", lazy=True)
    ativos = db.relationship("Ativo", backref="cliente", lazy=True)

    def __repr__(self):
        return f"<Cliente {self.nome}>"


# --------------------------------------------------------
# ATIVOS (embarcações, máquinas etc.)
# --------------------------------------------------------
class Ativo(db.Model):
    __tablename__ = "ativos"

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)

    nome = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(120), nullable=True)
    imei = db.Column(db.String(50), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    # TELEMETRIA AVANÇADA
    horas_offset = db.Column(db.Float, default=0.0)
    horas_sistema = db.Column(db.Float, default=0.0)
    horas_paradas = db.Column(db.Float, default=0.0)
    ultimo_estado_motor = db.Column(db.Integer, default=0)  # 0 desligado / 1 ligado
    total_ignicoes = db.Column(db.Integer, default=0)
    ultima_atualizacao = db.Column(db.DateTime, nullable=True)

    # localização
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Ativo {self.nome}>"
