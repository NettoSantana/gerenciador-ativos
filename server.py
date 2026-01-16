import os
import sqlite3
from datetime import date
from flask import Flask, request, session, redirect, url_for, render_template_string
from flask_login import LoginManager, current_user
from gerenciador_ativos.config import Config
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario, Ativo

# importa modelos de preventiva para registrar no metadata
from gerenciador_ativos import preventiva_models  # noqa

# Blueprints
from gerenciador_ativos.auth.routes import auth_bp
from gerenciador_ativos.dashboards.geral import dashboard_geral_bp
from gerenciador_ativos.usuarios.routes import usuarios_bp
from gerenciador_ativos.clientes.routes import clientes_bp
from gerenciador_ativos.ativos.routes import ativos_bp
from gerenciador_ativos.portal.routes import portal_bp
from gerenciador_ativos.ativos.painel import painel_bp
from gerenciador_ativos.api.ativos.routes_dados import api_ativos_dados_bp
from gerenciador_ativos.api.monitoramento.routes import monitoramento_bp
from gerenciador_ativos.api.ativos import api_ativos_bp

# 🔥 API DO DASHBOARD GERAL (TV)
from gerenciador_ativos.api.dashboard.routes import dashboard_api_bp

# 🧰 ALMOXARIFADO
from gerenciador_ativos.almoxarifado.routes import almoxarifado_bp


def ensure_sqlite_schema(db_path: str):
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='ativos';
    """)
    if not cur.fetchone():
        conn.close()
        return

    cur.execute("PRAGMA table_info(ativos);")
    colunas = [row[1] for row in cur.fetchall()]

    # já existia no seu projeto
    if "consumo_lph" not in colunas:
        cur.execute("ALTER TABLE ativos ADD COLUMN consumo_lph REAL DEFAULT 0;")

    # ✅ novo: suporte Mobiltracker
    if "tracker_id" not in colunas:
        cur.execute("ALTER TABLE ativos ADD COLUMN tracker_id TEXT;")

    # ✅ novo: define qual identificador usar por ativo ("mobiltracker" ou "imei")
    if "tracking_provider" not in colunas:
        cur.execute("ALTER TABLE ativos ADD COLUMN tracking_provider TEXT DEFAULT 'mobiltracker';")

    # ✅ NOVO: tabela operacional para "Cotista do Dia"
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cotista_dia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            ativo_id INTEGER NOT NULL,
            cotista TEXT NOT NULL,
            observacao TEXT,
            atualizado_em TEXT NOT NULL,
            UNIQUE(data, ativo_id)
        );
    """)

    conn.commit()
    conn.close()


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # --------------------------------------------------
    # CONFIG
    # --------------------------------------------------
    app.config.from_object(Config)

    app.config["SECRET_KEY"] = getattr(
        Config,
        "SECRET_KEY",
        os.environ.get("SECRET_KEY", "dev-secret-key-fixo")
    )

    # --------------------------------------------------
    # SQLITE
    # --------------------------------------------------
    INSTANCE_PATH = "/app/instance"
    os.makedirs(INSTANCE_PATH, exist_ok=True)
    DB_PATH = os.path.join(INSTANCE_PATH, "gerenciador_ativos.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --------------------------------------------------
    # EXTENSIONS
    # --------------------------------------------------
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return Usuario.query.get(int(user_id))
        except Exception:
            return None

    # 🔎 DEBUG: quando o Flask-Login barra acesso (ex: /almoxarifado/)
    @login_manager.unauthorized_handler
    def _unauthorized():
        # logs aparecem no Railway
        print("=== UNAUTHORIZED (Flask-Login) ===")
        print("path:", request.path)
        print("method:", request.method)
        print("remote:", request.headers.get("X-Forwarded-For") or request.remote_addr)
        print("proto:", request.headers.get("X-Forwarded-Proto"))
        print("host:", request.host)
        print("cookies:", "session" in request.cookies)
        print("session_keys:", list(session.keys()))
        print("session_user_id:", session.get("_user_id"))
        print("current_user.is_authenticated:", getattr(current_user, "is_authenticated", None))
        print("=== /UNAUTHORIZED ===")
        return login_manager.unauthorized()

    # --------------------------------------------------
    # OPERAÇÃO: COTISTA DO DIA (tela simples, funcional)
    # --------------------------------------------------
    def _operacao_permitida():
        # mantém o padrão do seu menu: só admin/gerente
        return session.get("user_tipo") in ["admin", "gerente"]

    def _db_conn():
        return sqlite3.connect(DB_PATH)

    @app.route("/operacao", methods=["GET"])
    def operacao_home():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not _operacao_permitida():
            return redirect(url_for("dashboard_geral.dashboard_gerente"))

        dia = request.args.get("data") or date.today().isoformat()

        with app.app_context():
            ativos = Ativo.query.filter_by(ativo=True).order_by(Ativo.nome.asc()).all()

        # carrega lançamentos do dia
        conn = _db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.data, c.ativo_id, c.cotista, IFNULL(c.observacao, ''), c.atualizado_em
            FROM cotista_dia c
            WHERE c.data = ?
            ORDER BY c.atualizado_em DESC;
        """, (dia,))
        rows = cur.fetchall()
        conn.close()

        # map ativo_id -> nome (pra renderizar bonito)
        ativo_nome = {a.id: a.nome for a in ativos}
        lançamentos = [
            {
                "data": r[0],
                "ativo_id": r[1],
                "ativo_nome": ativo_nome.get(r[1], f"Ativo #{r[1]}"),
                "cotista": r[2],
                "observacao": r[3],
                "atualizado_em": r[4],
            }
            for r in rows
        ]

        html = """
        {% extends "base.html" %}
        {% block title %}Operação{% endblock %}
        {% block content %}
        <div class="page" style="max-width:1100px;margin:0 auto;">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
            <div>
              <h1 style="margin:0;">Operação</h1>
              <div style="color:#94a3b8;font-size:13px;margin-top:4px;">
                Cotista do Dia — lançamento diário por embarcação
              </div>
            </div>
          </div>

          <div class="card" style="margin-top:16px;padding:18px;border-radius:16px;">
            <form method="post" action="/operacao/cotista" style="display:grid;grid-template-columns:repeat(12,1fr);gap:12px;">
              <div style="grid-column:span 3;">
                <label style="display:block;color:#94a3b8;font-size:12px;letter-spacing:.08em;text-transform:uppercase;">Data</label>
                <input name="data" value="{{ dia }}" type="date" class="input" style="width:100%;" required>
              </div>

              <div style="grid-column:span 5;">
                <label style="display:block;color:#94a3b8;font-size:12px;letter-spacing:.08em;text-transform:uppercase;">Embarcação</label>
                <select name="ativo_id" class="input" style="width:100%;" required>
                  <option value="">Selecione…</option>
                  {% for a in ativos %}
                    <option value="{{ a.id }}">{{ a.nome }}</option>
                  {% endfor %}
                </select>
              </div>

              <div style="grid-column:span 4;">
                <label style="display:block;color:#94a3b8;font-size:12px;letter-spacing:.08em;text-transform:uppercase;">Cotista do dia</label>
                <input name="cotista" placeholder="Ex.: João / Maria / BoatLUX" class="input" style="width:100%;" required>
              </div>

              <div style="grid-column:span 12;">
                <label style="display:block;color:#94a3b8;font-size:12px;letter-spacing:.08em;text-transform:uppercase;">Observação (opcional)</label>
                <input name="observacao" placeholder="Ex.: saiu cedo / retornou 17h / pendência..." class="input" style="width:100%;">
              </div>

              <div style="grid-column:span 12;display:flex;gap:10px;justify-content:flex-end;">
                <button class="btn-primary" type="submit">Salvar lançamento</button>
              </div>
            </form>
          </div>

          <div class="card" style="margin-top:16px;padding:18px;border-radius:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
              <h2 style="margin:0;font-size:16px;color:#38bdf8;text-transform:uppercase;">Lançamentos do dia</h2>

              <form method="get" action="/operacao" style="display:flex;gap:8px;align-items:center;">
                <input type="date" name="data" value="{{ dia }}" class="input">
                <button class="btn-ghost" type="submit">Ver</button>
              </form>
            </div>

            {% if lancamentos|length == 0 %}
              <div style="margin-top:12px;color:#94a3b8;">Nenhum lançamento para esta data.</div>
            {% else %}
              <table class="table" style="width:100%;margin-top:12px;">
                <thead>
                  <tr>
                    <th style="text-align:left;padding:10px;">Embarcação</th>
                    <th style="text-align:left;padding:10px;">Cotista</th>
                    <th style="text-align:left;padding:10px;">Obs</th>
                    <th style="text-align:left;padding:10px;">Atualizado</th>
                  </tr>
                </thead>
                <tbody>
                  {% for l in lancamentos %}
                    <tr>
                      <td style="padding:10px;">{{ l.ativo_nome }}</td>
                      <td style="padding:10px;">{{ l.cotista }}</td>
                      <td style="padding:10px;">{{ l.observacao or "—" }}</td>
                      <td style="padding:10px;">{{ l.atualizado_em }}</td>
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            {% endif %}
          </div>

        </div>
        {% endblock %}
        """
        return render_template_string(html, ativos=ativos, dia=dia, lancamentos=lançamentos)

    @app.route("/operacao/cotista", methods=["POST"])
    def operacao_salvar_cotista():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not _operacao_permitida():
            return redirect(url_for("dashboard_geral.dashboard_gerente"))

        dia = (request.form.get("data") or "").strip()
        ativo_id = (request.form.get("ativo_id") or "").strip()
        cotista = (request.form.get("cotista") or "").strip()
        observacao = (request.form.get("observacao") or "").strip()

        if not dia or not ativo_id or not cotista:
            return redirect(f"/operacao?data={dia or date.today().isoformat()}")

        # UPSERT (data + ativo_id)
        conn = _db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO cotista_dia (data, ativo_id, cotista, observacao, atualizado_em)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(data, ativo_id) DO UPDATE SET
              cotista=excluded.cotista,
              observacao=excluded.observacao,
              atualizado_em=datetime('now');
        """, (dia, int(ativo_id), cotista, observacao))
        conn.commit()
        conn.close()

        return redirect(f"/operacao?data={dia}")

    # --------------------------------------------------
    # INIT DB
    # --------------------------------------------------
    if os.environ.get("RUN_DB_INIT") == "1":
        with app.app_context():
            db.create_all()

            admin = Usuario.query.filter_by(email="admin@admin.com").first()
            if not admin:
                admin = Usuario(
                    nome="Administrador",
                    email="admin@admin.com",
                    tipo="admin",
                    ativo=True
                )
                admin.set_password("admin123")
                db.session.add(admin)
                db.session.commit()

    # --------------------------------------------------
    # BLUEPRINTS
    # --------------------------------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_geral_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(ativos_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(painel_bp)
    app.register_blueprint(monitoramento_bp)
    app.register_blueprint(api_ativos_dados_bp)
    app.register_blueprint(api_ativos_bp)

    # 🧰 ALMOXARIFADO
    app.register_blueprint(almoxarifado_bp)

    # 🔥 API DO DASHBOARD GERAL
    app.register_blueprint(dashboard_api_bp)

    # --------------------------------------------------
    # STARTUP
    # --------------------------------------------------
    with app.app_context():
        if os.path.exists(DB_PATH):
            ensure_sqlite_schema(DB_PATH)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
