from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import AlmoxItem


almoxarifado_bp = Blueprint(
    "almoxarifado",
    __name__,
    url_prefix="/almoxarifado",
)


def _to_float(v, default=0.0):
    try:
        if v is None:
            return default
        s = str(v).strip().replace(",", ".")
        if s == "":
            return default
        return float(s)
    except Exception:
        return default


@almoxarifado_bp.route("/", methods=["GET"])
@login_required
def index():
    itens = (
        AlmoxItem.query
        .order_by(AlmoxItem.ativo.desc(), AlmoxItem.nome.asc())
        .all()
    )
    return render_template("almoxarifado/index.html", itens=itens)


@almoxarifado_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        categoria = (request.form.get("categoria") or "").strip() or None
        unidade = (request.form.get("unidade") or "").strip()
        estoque_atual = _to_float(request.form.get("estoque_atual"), default=0.0)

        if not nome:
            flash("Informe o nome do item.", "danger")
            return render_template("almoxarifado/novo.html")

        if not unidade:
            flash("Informe a unidade (ex: peça, litro, metro, kg).", "danger")
            return render_template("almoxarifado/novo.html")

        existe = AlmoxItem.query.filter(AlmoxItem.nome.ilike(nome)).first()
        if existe:
            flash("Já existe um item com esse nome.", "danger")
            return render_template("almoxarifado/novo.html")

        item = AlmoxItem(
            nome=nome,
            categoria=categoria,
            unidade=unidade,
            estoque_atual=estoque_atual,
            ativo=True,
        )

        db.session.add(item)
        db.session.commit()

        flash("Item criado com sucesso.", "success")
        return redirect(url_for("almoxarifado.index"))

    return render_template("almoxarifado/novo.html")
