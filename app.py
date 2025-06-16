from flask import Flask, session
from dotenv import load_dotenv
from os import getenv

from app.routes import routes
from app.database import db
from authlib.integrations.flask_client import OAuth

# Laad .env file
load_dotenv()

# Initialiseer Flask
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = getenv("APP_SECRET_KEY")

# databank init
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db.init_app(app)

# 0Auth instellen
oauth = OAuth(app)
app.oauth=oauth
oauth.register(
    "auth0",
    client_id=getenv("AUTH0_CLIENT_ID"),
    client_secret=getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


# Blueprints
app.register_blueprint(routes)

if __name__ == '__main__':
    from app.database.models import Base
    from app.database.session import engine

    Base.metadata.create_all(bind=engine)
    app.run(host='0.0.0.0', port=8000, debug=True)
