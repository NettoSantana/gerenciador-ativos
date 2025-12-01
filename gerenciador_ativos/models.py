from gerenciador_ativos.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# --------------------------------------------------------
# USUÁRIO DO SISTEMA (ADMIN, GERENTE, TÉCNICO, CLIENTE)
# --------------------------------------------------------
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)

    tipo = db.Column(db.String(50), default="gerente")  # admin / gerente / cliente
    ativo = db.Column(db.Boolean, default=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=True)

    # --------------------------------------------------------
    # MÉTODOS DE SENHA — PADRÃO FLASK
    # --------------------------------------------------------
    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

    # --------------------------------------------------------
    # MÉTODOS DE APOIO
    # --------------------------------------------------------
    def is_interno(self):
        return self.tipo in ["admin", "gerente"]

    def __repr__(self):
        return f"<Usuario {self.email}>"
