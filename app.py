from flask import Flask, session
from dotenv import load_dotenv
from os import getenv

from app.routes import routes
from authlib.integrations.flask_client import OAuth

# Laad .env file
load_dotenv()


# Initialiseer Flask
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Secret key instellen voor sessies
app.secret_key = getenv("APP_SECRET_KEY")

# 0Auth instellen
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

app.oauth=oauth

# Registreer je Blueprint-routes
app.register_blueprint(routes)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

