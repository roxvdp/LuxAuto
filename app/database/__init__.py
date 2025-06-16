from flask_sqlalchemy import SQLAlchemy

# Initialiseer SQLAlchemy object
db = SQLAlchemy()

def init_app(app):
    db.init_app(app)
