from flask import render_template, request, redirect, url_for, flash
from gerenciador_ativos.ativos import ativos_bp
from gerenciador_ativos.models import Ativo, Cliente
from gerenciador_ativos.auth.decorators import login_required, role_required
from gerenciador_ativos.ativos.service import (
    criar_ativo, atualizar_ativo,
    desativar_ativo, ativar_ativo
)


@ativos_bp.route("/")
@login_required
@role_required(["admin", "gerente"])
def lista():
    ativos = Ativo.query.order_by(Ativo.nome).all()
    return render_template("ativos/lista.html", ativos=ativos)


@ativos_bp.route("/novo", methods=["GET", "POST"])
@login_required
@role_required(["admin", "gerente"])
def novo():
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id")
        nome = request.form.get("nome")
        categoria = request.form.get("categoria")
        tipo = request.form.get("tipo")
        modelo = request.form.get("modelo")
        numero_serie = request.form.get("numero_serie")
        codigo_interno = request.form.get("codigo_interno")
        localizacao = request.form.get("localizacao")
        status_operacional = request.form.get("status_operacional")
        observacoes = request.form.get("observacoes")

        if not cliente_id:
            flash("Selecione um cliente.", "danger")
            return redirect(url_for("ativos.novo"))

        criar_ativo(
            cliente_id=int(cliente_id),
            nome=nome,
            categoria=categoria,
            tipo=tipo,
            modelo=modelo,
            numero_serie=numero_serie,
            codigo_interno=codigo_interno,
            localizacao=localizacao,
            status_operacional=status_operacional,
            observacoes=observacoes
        )

        flash("Ativo criado com sucesso!", "success")
        return redirect(url_for("ativos.lista"))

    return render_template("ativos/novo.html", clientes=clientes)


@ativos_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
@role_required(["admin", "gerente"])
def editar(id):
    ativo = Ativo.query.get_or_404(id)
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id")
        nome = request.form.get("nome")
        categoria = request.form.get("categoria")
        tipo = request.form.get("tipo")
        modelo = request.form.get("modelo")
        numero_serie = request.form.get("numero_serie")
        codigo_interno = request.form.get("codigo_interno")
        localizacao = request.form.get("localizacao")
        status_operacional = request.form.get("status_operacional")
        observacoes = request.form.get("observacoes")

        if not cliente_id:
            flash("Selecione um cliente.", "danger")
            return redirect(url_for("ativos.editar", id=id))

        atualizar_ativo(
            ativo,
            cliente_id=int(cliente_id),
            nome=nome,
            categoria=categoria,
            tipo=tipo,
            modelo=modelo,
            numero_serie=numero_serie,
            codigo_interno=codigo_interno,
            localizacao=localizacao,
            status_operacional=status_operacional,
            observacoes=observacoes
        )

        flash("Ativo atualizado!", "success")
        return redirect(url_for("ativos.lista"))

    return render_template("ativos/editar.html", ativo=ativo, clientes=clientes)


@ativos_bp.route("/desativar/<int:id>")
@login_required
@role_required(["admin", "gerente"])
def desativar(id):
    ativo = Ativo.query.get_or_404(id)
    desativar_ativo(ativo)
    flash("Ativo desativado.", "warning")
    return redirect(url_for("ativos.lista"))


@ativos_bp.route("/ativar/<int:id>")
@login_required
@role_required(["admin", "gerente"])
def ativar(id):
    ativo = Ativo.query.get_or_404(id)
    ativar_ativo(ativo)
    flash("Ativo ativado!", "success")
    return redirect(url_for("ativos.lista"))
