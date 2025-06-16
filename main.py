from flask import Flask, session
from dotenv import load_dotenv
from os import getenv

from app.routes import routes
from authlib.integrations.flask_client import OAuth
from app.database import init_app as init_db  # ✅ toegevoegd

# Laad .env file
load_dotenv()

# Initialiseer Flask
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = getenv("APP_SECRET_KEY")

# Database koppelen
init_db(app)  # ✅ toegevoegd

# Auth0
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=getenv("AUTH0_CLIENT_ID"),
    client_secret=getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)
app.oauth = oauth

# Blueprints
app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
