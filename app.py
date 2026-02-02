from flask import Flask
from models.models import db
from routes.auth import auth_bp
from routes.tickets import tickets_bp

import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'helpdesk-secret-key'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'helpdesk.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Register Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(tickets_bp)
from routes.admin import admin_bp
app.register_blueprint(admin_bp)


@app.route("/")
def home():
    return "Helpdesk System Running!"

if __name__ == "__main__":
    app.run(debug=True)
