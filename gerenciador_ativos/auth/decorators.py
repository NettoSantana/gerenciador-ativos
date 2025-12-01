from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Faça login para acessar esta página.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def role_required(roles):
    """roles: lista de tipos permitidos, ex: ['admin', 'gerente']"""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            user_tipo = session.get("user_tipo")
            if user_tipo not in roles:
                flash("Você não tem permissão para acessar esta área.", "danger")
                return redirect(url_for("dashboards.home"))
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


# ------------------------------------------------------
# ADICIONAR ESTA FUNÇÃO ↓↓↓
# ------------------------------------------------------
def gerente_required(view_func):
    return role_required(["admin", "gerente"])(view_func)
