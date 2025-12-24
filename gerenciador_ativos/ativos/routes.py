from flask import Blueprint, render_template, request, redirect, url_for, flash
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Ativo, Cliente
from gerenciador_ativos.auth.decorators import login_required
from datetime import datetime

ativos_bp = Blueprint("ativos", __name__, url_prefix="/ativos")


# ----------------------------------------------------------------------
# LISTA DE ATIVOS
# ----------------------------------------------------------------------
@ativos_bp.route("/")
@login_required
def lista():
    ativos = Ativo.query.all()
    return render_template("ativos/lista.html", ativos=ativos)


# ----------------------------------------------------------------------
# NOVO ATIVO
# ----------------------------------------------------------------------
@ativos_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    clientes = Cliente.query.all()

    if request.method == "POST":
        try:
            consumo_litros_hora = float(request.form.get("consumo_litros_hora") or 0)

            ativo = Ativo(
                cliente_id=request.form["cliente_id"],
                nome=request.form["nome"],
                categoria=request.form["categoria"],
                imei=request.form["imei"],
                observacoes=request.form.get("observacoes"),
                consumo_litros_hora=consumo_litros_hora,
                criado_em=datetime.utcnow(),
            )

            db.session.add(ativo)
            db.session.commit()

            flash("Ativo cadastrado com sucesso.", "success")
            return redirect(url_for("ativos.lista"))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar ativo: {e}", "error")

    return render_template("ativos/novo.html", clientes=clientes)


# ----------------------------------------------------------------------
# EDITAR ATIVO
# ----------------------------------------------------------------------
@ativos_bp.route("/editar/<int:ativo_id>", methods=["GET", "POST"])
@login_required
def editar(ativo_id):
    ativo = Ativo.query.get_or_404(ativo_id)
    clientes = Cliente.query.all()

    if request.method == "POST":
        try:
            ativo.cliente_id = request.form["cliente_id"]
            ativo.nome = request.form["nome"]
            ativo.categoria = request.form["categoria"]
            ativo.imei = request.form["imei"]
            ativo.observacoes = request.form.get("observacoes")

            ativo.consumo_litros_hora = float(
                request.form.get("consumo_litros_hora") or 0
            )

            db.session.commit()

            flash("Ativo atualizado com sucesso.", "success")
            return redirect(url_for("ativos.lista"))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar ativo: {e}", "error")

    return render_template(
        "ativos/editar.html",
        ativo=ativo,
        clientes=clientes,
    )


# ----------------------------------------------------------------------
# EXCLUIR ATIVO
# ----------------------------------------------------------------------
@ativos_bp.route("/excluir/<int:ativo_id>", methods=["POST"])
@login_required
def excluir(ativo_id):
    ativo = Ativo.query.get_or_404(ativo_id)

    try:
        db.session.delete(ativo)
        db.session.commit()
        flash("Ativo excluído com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir ativo: {e}", "error")

    return redirect(url_for("ativos.lista"))
