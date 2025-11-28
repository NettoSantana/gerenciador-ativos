from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from gerenciador_ativos.extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # admin, gerente, manutencao, financeiro, fiscal, cliente
    cliente_id = db.Column(db.Integer, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def set_password(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    def is_interno(self) -> bool:
        return self.tipo in ["admin", "gerente", "manutencao", "financeiro", "fiscal"]

    def __repr__(self) -> str:
        return f"<Usuario {self.email} ({self.tipo})>"
