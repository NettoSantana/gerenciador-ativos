from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import AlmoxItem

almoxarifado_bp = Blueprint(
    "almoxarifado",
    __name__,
    url_prefix="/almoxarifado"
)


@almoxarifado_bp.route("/", methods=["GET"])
@login_required
def index():
    q = (request.args.get("q") or "").strip()

    query = AlmoxItem.query.filter_by(ativo=True)

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                AlmoxItem.nome.ilike(like),
                AlmoxItem.categoria.ilike(like),
                AlmoxItem.unidade.ilike(like),
            )
        )

    itens = query.order_by(AlmoxItem.nome.asc()).all()
    return render_template("almoxarifado/index.html", itens=itens, q=q)


@almoxarifado_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        unidade = (request.form.get("unidade") or "").strip()
        categoria = (request.form.get("categoria") or "").strip() or None
        estoque_raw = (request.form.get("estoque_atual") or "").strip()

        if not nome or not unidade:
            flash("Preencha Nome e Unidade.", "danger")
            return redirect(url_for("almoxarifado.novo"))

        try:
            estoque_atual = float(estoque_raw.replace(",", ".")) if estoque_raw else 0.0
        except ValueError:
            flash("Estoque inicial inválido.", "danger")
            return redirect(url_for("almoxarifado.novo"))

        item = AlmoxItem(
            nome=nome,
            unidade=unidade,
            categoria=categoria,
            estoque_atual=estoque_atual,
            ativo=True,
        )

        try:
            db.session.add(item)
            db.session.commit()
            flash("Item criado com sucesso.", "success")
            return redirect(url_for("almoxarifado.index"))
        except IntegrityError:
            db.session.rollback()
            flash("Já existe um item com esse nome.", "danger")
            return redirect(url_for("almoxarifado.novo"))

    return render_template("almoxarifado/novo.html")


@almoxarifado_bp.route("/<int:item_id>/editar", methods=["GET", "POST"])
@login_required
def editar(item_id: int):
    item = AlmoxItem.query.get_or_404(item_id)

    if not item.ativo:
        flash("Esse item está inativo.", "warning")
        return redirect(url_for("almoxarifado.index"))

    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        unidade = (request.form.get("unidade") or "").strip()
        categoria = (request.form.get("categoria") or "").strip() or None
        estoque_raw = (request.form.get("estoque_atual") or "").strip()

        if not nome or not unidade:
            flash("Preencha Nome e Unidade.", "danger")
            return redirect(url_for("almoxarifado.editar", item_id=item_id))

        try:
            estoque_atual = float(estoque_raw.replace(",", ".")) if estoque_raw else 0.0
        except ValueError:
            flash("Estoque inválido.", "danger")
            return redirect(url_for("almoxarifado.editar", item_id=item_id))

        item.nome = nome
        item.unidade = unidade
        item.categoria = categoria
        item.estoque_atual = estoque_atual

        try:
            db.session.commit()
            flash("Item atualizado.", "success")
            return redirect(url_for("almoxarifado.index"))
        except IntegrityError:
            db.session.rollback()
            flash("Já existe um item com esse nome.", "danger")
            return redirect(url_for("almoxarifado.editar", item_id=item_id))

    return render_template("almoxarifado/editar.html", item=item)


@almoxarifado_bp.route("/<int:item_id>/excluir", methods=["POST"])
@login_required
def excluir(item_id: int):
    item = AlmoxItem.query.get_or_404(item_id)

    if not item.ativo:
        flash("Item já está inativo.", "warning")
        return redirect(url_for("almoxarifado.index"))

    # soft delete (mantém histórico/movimentos)
    item.ativo = False
    db.session.commit()

    flash("Item excluído (inativado).", "success")
    return redirect(url_for("almoxarifado.index"))
