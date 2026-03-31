from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, abort, jsonify, send_from_directory
from flask_cors import CORS
from pymongo.errors import ServerSelectionTimeoutError

from backend.config import Config
from backend.extensions import create_indexes


def _validate_runtime_config(app):
    secret = app.config.get("JWT_SECRET_KEY", "")
    if not secret or secret == "change-me!":
        raise RuntimeError(
            "JWT_SECRET_KEY is missing or insecure. Set a strong value in backend/.env "
            "or your deployment environment before starting the app."
        )


def _configure_cors(app):
    origins = app.config.get("CORS_ORIGINS", [])
    if not origins:
        return

    CORS(app, resources={
        r"/api/*": {
            "origins": origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })


def _register_blueprints(app):
    from backend.routes.admin import admin_bp
    from backend.routes.auth import auth_bp
    from backend.routes.tickets import tickets_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tickets_bp, url_prefix="/api/tickets")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")


def _register_system_routes(app):
    @app.get("/api/health")
    def health():
        frontend_ready = (Path(app.config["FRONTEND_DIR"]) / "index.html").exists()
        return jsonify({
            "success": True,
            "message": "OK",
            "data": {
                "status": "healthy",
                "frontend_ready": frontend_ready,
            },
        })


def _register_frontend_routes(app):
    frontend_dir = Path(app.config["FRONTEND_DIR"])
    if not frontend_dir.exists():
        return

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path.startswith("api/"):
            abort(404)

        if path and (frontend_dir / path).is_file():
            return send_from_directory(frontend_dir, path)

        return send_from_directory(frontend_dir, "index.html")


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)
    _validate_runtime_config(app)

    _configure_cors(app)
    _register_blueprints(app)
    _register_system_routes(app)
    _register_frontend_routes(app)

    with app.app_context():
        try:
            create_indexes()
        except ServerSelectionTimeoutError as exc:
            raise RuntimeError(
                "MongoDB is not reachable. Start MongoDB or update MONGO_URI in backend/.env "
                "before running the app."
            ) from exc

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, port=5000)
