# app/database/__init__.py

from flask_sqlalchemy import SQLAlchemy
from os import getenv
from dotenv import load_dotenv

# .env inladen (voor zowel Flask als Alembic)
load_dotenv()

# Initialiseer SQLAlchemy object
db = SQLAlchemy()

def init_app(app):
    # Stel DB-URI in als deze nog niet in app.config zit
    if "SQLALCHEMY_DATABASE_URI" not in app.config:
        app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")

    # Optioneel: geen waarschuwingen
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Koppel db aan Flask-app
    db.init_app(app)
