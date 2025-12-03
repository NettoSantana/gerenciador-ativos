import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(os.path.dirname(BASE_DIR), "instance")

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Se tiver DATABASE_URL (Railway/Postgres), usa ele.
    # Caso contrário, usa SQLite persistente em /instance/
    if os.environ.get("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(INSTANCE_DIR, 'gerenciador_ativos.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
