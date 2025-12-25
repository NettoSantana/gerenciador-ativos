import os
import sqlite3
from flask import Flask
from gerenciador_ativos.config import Config
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario

# importa modelos de preventiva para registrar no metadata
from gerenciador_ativos import preventiva_models  # noqa

# Blueprints
from gerenciador_ativos.auth.routes import auth_bp
from gerenciador_ativos.dashboards.routes import dashboards_bp
from gerenciador_ativos.usuarios.routes import usuarios_bp
from gerenciador_ativos.clientes.routes import clientes_bp
from gerenciador_ativos.ativos.routes import ativos_bp
from gerenciador_ativos.portal.routes import portal_bp
from gerenciador_ativos.ativos.painel import painel_bp
from gerenciador_ativos.api.ativos.routes_dados import api_ativos_dados_bp
from gerenciador_ativos.api.monitoramento.routes import monitoramento_bp
from gerenciador_ativos.api.ativos import api_ativos_bp


def ensure_sqlite_schema(db_path: str):
    """
    Garante que colunas novas existam no SQLite
    sem apagar dados existentes.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(ativos);")
    colunas = [row[1] for row in cur.fetchall()]

    if "consumo_lph" not in colunas:
        print(">>> Criando coluna consumo_lph")
        cur.execute(
            "ALTER TABLE ativos ADD COLUMN consumo_lph REAL DEFAULT 0;"
        )

    conn.commit()
    conn.close()


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # inicializa banco
    db.init_app(app)

    # registra blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboards_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(ativos_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(painel_bp)
    app.register_blueprint(monitoramento_bp)
    app.register_blueprint(api_ativos_dados_bp)
    app.register_blueprint(api_ativos_bp)

    with app.app_context():
        instance_path = os.path.join(os.getcwd(), "instance")
        os.makedirs(instance_path, exist_ok=True)

        db_path = os.path.join(instance_path, "gerenciador_ativos.db")

        if not os.path.exists(db_path):
            print(">>> Banco não encontrado — criando novo banco...")
            db.create_all()

            admin = Usuario(
                nome="Administrador",
                email="admin@admin.com",
                tipo="admin",
                ativo=True
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print(">>> Usuário admin criado")
        else:
            print(">>> Banco existente — validando schema")
            ensure_sqlite_schema(db_path)

    return app


# garante diretório instance antes de subir
os.makedirs("instance", exist_ok=True)

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
