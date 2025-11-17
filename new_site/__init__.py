import os
from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()

def create_app() -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///./instance/app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Ensure sqlite directory exists
    try:
        uri = app.config['SQLALCHEMY_DATABASE_URI']
        if uri.startswith('sqlite:///'):
            import pathlib
            p = pathlib.Path(uri.replace('sqlite:///', '', 1))
            if not p.is_absolute():
                base = pathlib.Path(__file__).resolve().parent.parent
                p = (base / p).resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    db.init_app(app)

    from . import models  # noqa: F401
    from .routes_auth import auth_bp
    from .routes_assets import assets_bp
    from .routes_types import types_bp
    from .routes_maintenance import maint_bp
    from .routes_audit import audit_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(types_bp)
    app.register_blueprint(maint_bp)
    app.register_blueprint(audit_bp)

    from flask import render_template, session, redirect, url_for

    @app.route('/')
    def index():
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return render_template('index.html')

    return app


