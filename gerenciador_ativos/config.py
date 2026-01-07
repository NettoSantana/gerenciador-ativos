import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(os.path.dirname(BASE_DIR), "instance")

class Config:
    # --------------------------------------------------
    # SECURITY
    # --------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Cookies de sessão — ESSENCIAL para não perder login
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Em produção (Railway usa HTTPS por trás)
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------
    if os.environ.get("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{os.path.join(INSTANCE_DIR, 'gerenciador_ativos.db')}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
