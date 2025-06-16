import os
from flask import Flask
from dotenv import load_dotenv
from app.database import init_app as init_database
from app.routes import routes  # 👈 jouw blueprint (met alle pagina's)

load_dotenv()  # Laad de .env omgeving

def create_app():
    app = Flask(__name__)

    # Geheim en databaseconfiguratie worden in database/init_app geregeld via .env
    init_database(app)

    # Blueprint registreren (zoals /, /login, /auto, /admin, ...)
    app.register_blueprint(routes)

    return app
