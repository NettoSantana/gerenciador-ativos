import os
from flask import Flask
from gerenciador_ativos.config import Config
from gerenciador_ativos.extensions import db

# 🔥 IMPORT CORRETO DO USUÁRIO
from gerenciador_ativos.usuarios.models import Usuario

# importa modelos de preventiva para aparecer nas tabelas
from gerenciador_ativos import preventiva_models  # noqa

# Blueprints existentes
from gerenciador_ativos.auth.routes import auth_bp
from gerenciador_ativos.dashboards.routes import dashboards_bp
from gerenciador_ativos.usuarios.routes import usuarios_bp
from gerenciador_ativos.clientes.routes import clientes_bp
from gerenciador_ativos.ativos.routes import ativos_bp
from gerenciador_ativos.portal.routes import portal_bp
from gerenciador_ativos.ativos.painel import painel_bp
from gerenciador_ativos.api.ativos.routes_dados import api_ativos_dados_bp

# novos blueprints
from gerenciador_ativos.api.monitoramento.routes import monitoramento_bp
from gerenciador_ativos.api.ativos import api_ativos_bp


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # extensão do banco
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

    # cria banco apenas se não existir
    with app.app_context():
        instance_path = os.path.join(os.getcwd(), "instance")
        os.makedirs(instance_path, exist_ok=True)

        db_path = os.path.join(instance_path, "gerenciador_ativos.db")

        if not os.path.exists(db_path):
            print(">>> Banco não encontrado — criando novo banco...")
            db.create_all()

            # cria admin apenas na criação do banco
            admin = Usuario(
                nome="Administrador",
                email="admin@admin.com",
                tipo="admin",
                ativo=True
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print(">>> Usuário admin criado: email=admin@admin.com | senha=admin123")
        else:
            print(">>> Banco já existe — não será recriado.")

    # ----------------------------------------------------------------------
    # 🔥 ROTA PARA CRIAR A COLUNA horas_offset (UMA VEZ SÓ)
    # ----------------------------------------------------------------------
    @app.route("/fix-db")
    def fix_db():
        import sqlite3

        db_path = os.path.join(os.getcwd(), "instance", "gerenciador_ativos.db")

        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                "ALTER TABLE ativos ADD COLUMN horas_offset REAL DEFAULT 0;"
            )
            conn.commit()
            conn.close()
            return "Coluna horas_offset criada com sucesso!"
        except Exception as e:
            return f"Erro ao criar coluna (provavelmente já existe): {e}"

    # ----------------------------------------------------------------------
    # 🔥 ROTA PARA CRIAR A COLUNA consumo_litros_hora (UMA VEZ SÓ)
    # ----------------------------------------------------------------------
    @app.route("/fix-db-consumo")
    def fix_db_consumo():
        import sqlite3

        db_path = os.path.join(os.getcwd(), "instance", "gerenciador_ativos.db")

        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                "ALTER TABLE ativos ADD COLUMN consumo_litros_hora REAL DEFAULT 0.0;"
            )
            conn.commit()
            conn.close()
            return "Coluna consumo_litros_hora criada com sucesso!"
        except Exception as e:
            return f"Erro ao criar coluna (provavelmente já existe): {e}"

    return app


# garante o diretório instance ANTES de iniciar o app
os.makedirs("instance", exist_ok=True)

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
