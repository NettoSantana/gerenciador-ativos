from gerenciador_ativos.server import app, db
from gerenciador_ativos.models import Usuario

with app.app_context():
    print(">>> Criando tabelas...")
    db.create_all()

    admin = Usuario.query.filter_by(email="admin@admin.com").first()
    if not admin:
        print(">>> Criando usuário admin")
        admin = Usuario(
            nome="Administrador",
            email="admin@admin.com",
            tipo="admin",
            ativo=True
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

    print(">>> Banco inicializado com sucesso")
