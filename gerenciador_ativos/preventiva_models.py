from gerenciador_ativos.extensions import db


class PreventivaItem(db.Model):
    """
    Item de plano de preventiva vinculado a um ativo.

    - base: 'horas' ou 'dias'
    - intervalo: a cada quantas horas/dias a tarefa se repete
    - primeira_execucao: opcional (offset inicial em horas/dias)
    - avisar_antes: opcional (quanto antes avisar)
    """
    __tablename__ = "preventiva_itens"

    id = db.Column(db.Integer, primary_key=True)
    ativo_id = db.Column(db.Integer, nullable=False, index=True)

    nome = db.Column(db.String(120), nullable=False)

    # 'horas' ou 'dias'
    base = db.Column(db.String(10), nullable=False, default="horas")

    intervalo = db.Column(db.Float, nullable=False)          # horas ou dias
    primeira_execucao = db.Column(db.Float, nullable=True)   # horas ou dias
    avisar_antes = db.Column(db.Float, nullable=True)        # horas ou dias

    criado_em = db.Column(db.DateTime, server_default=db.func.now())
