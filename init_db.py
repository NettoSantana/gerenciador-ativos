from server import app, db
from models import Usuario

with app.app_context():
    print(">>> Criando todas as tabelas")
    db.create_all()

    if not Usuario.query.filter_by(email="admin@admin.com").first():
        print(">>> Criando admin")
        admin = Usuario(
            nome="Administrador",
            email="admin@admin.com",
            tipo="admin",
            ativo=True
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

    print(">>> Banco criado com sucesso")
