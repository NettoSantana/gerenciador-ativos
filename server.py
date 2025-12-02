from flask import Flask
from gerenciador_ativos.config import Config
from gerenciador_ativos.extensions import db
from gerenciador_ativos.models import Usuario

# Blueprints existentes
from gerenciador_ativos.auth.routes import auth_bp
from gerenciador_ativos.dashboards.routes import dashboards_bp
from gerenciador_ativos.usuarios.routes import usuarios_bp
from gerenciador_ativos.clientes.routes import clientes_bp
from gerenciador_ativos.ativos.routes import ativos_bp
from gerenciador_ativos.portal.routes import portal_bp
from gerenciador_ativos.ativos.painel import painel_bp
app.register_blueprint(painel_bp)


# 🔥 Novo: blueprint do monitoramento BrasilSat
from gerenciador_ativos.api.monitoramento.routes import monitoramento_bp

import os


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # extensão do banco
    db.init_app(app)

    # registro dos blueprints existentes
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboards_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(ativos_bp)
    app.register_blueprint(portal_bp)

    # registro do novo blueprint de monitoramento
    app.register_blueprint(monitoramento_bp)

    # cria o banco e cria admin se não existir
    with app.app_context():
        db.create_all()

        if Usuario.query.count() == 0:
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

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
