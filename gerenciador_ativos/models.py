from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from gerenciador_ativos.extensions import db


# =========================================
# MODELO: CLIENTE
# =========================================
class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)

    # PF ou PJ
    tipo = db.Column(db.String(10), nullable=False)

    # Nome (PF) ou Razão Social (PJ)
    nome = db.Column(db.String(255), nullable=False)

    # Nome fantasia (apenas PJ)
    nome_fantasia = db.Column(db.String(255), nullable=True)

    # CPF ou CNPJ
    cpf_cnpj = db.Column(db.String(20), nullable=False)

    telefone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    endereco = db.Column(db.String(255), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    ativo = db.Column(db.Boolean, default=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relacionamentos
    usuarios = db.relationship(
        "Usuario",
        backref="cliente",
        lazy=True,
        foreign_keys="Usuario.cliente_id"
    )

    ativos = db.relationship(
        "Ativo",
        backref="cliente",
        lazy=True,
        foreign_keys="Ativo.cliente_id"
    )

    def __repr__(self):
        return f"<Cliente {self.nome} ({self.tipo})>"


# =========================================
# MODELO: ATIVO
# =========================================
class Ativo(db.Model):
    __tablename__ = "ativos"

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=False
    )

    nome = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)  # Náutica, Industrial, Outros
    tipo = db.Column(db.String(100), nullable=True)       # Motor, Compressor, Embarcação, etc.
    modelo = db.Column(db.String(100), nullable=True)
    numero_serie = db.Column(db.String(100), nullable=True)
    codigo_interno = db.Column(db.String(100), nullable=True)
    localizacao = db.Column(db.String(255), nullable=True)

    status_operacional = db.Column(
        db.String(50),
        nullable=False,
        default="Operando"   # Operando, Parado, Em manutenção
    )

    observacoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Ativo {self.nome} ({self.categoria})>"


# =========================================
# MODELO: USUÁRIO
# =========================================
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # admin, gerente, manutencao, financeiro, fiscal, cliente

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=True
    )

    ativo = db.Column(db.Boolean, default=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Métodos
    def set_password(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    def is_interno(self) -> bool:
        return self.tipo in ["admin", "gerente", "manutencao", "financeiro", "fiscal"]

    def __repr__(self) -> str:
        return f"<Usuario {self.email} ({self.tipo})>"
