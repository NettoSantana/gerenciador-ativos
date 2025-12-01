from gerenciador_ativos.extensions import db


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)

    tipo = db.Column(db.String(50), nullable=False)              # PF ou PJ
    nome = db.Column(db.String(120), nullable=False)
    cpf_cnpj = db.Column(db.String(30), nullable=True)
    telefone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    endereco = db.Column(db.String(255), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    ativo = db.Column(db.Boolean, default=True)

    # Relacionamentos futuros:
    # ativos = db.relationship("Ativo", backref="cliente", lazy=True)

    def __repr__(self):
        return f"<Cliente {self.nome}>"
