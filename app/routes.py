from flask import Blueprint, render_template, session, redirect, url_for, current_app
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv


# Maak een blueprint
routes = Blueprint('routes', __name__)


# .env en Auth0 configuratie
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)



@routes.route("/login")
def login():
    oauth=current_app.oauth
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("routes.callback", _external=True)
    )


@routes.route("/callback", methods=["GET", "POST"])
def callback():
    oauth=current_app.oauth
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")


# Uitgelogd en redirected naar home page
@routes.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN") + "/v2/logout?" + urlencode(
            {
                "returnTo": url_for("routes.index", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# Terugkomst van ingelogde mensen of bezoekers
@routes.route('/')
def index():
    return render_template('index.html')

@routes.route('/auto')
def auto():
    return render_template('auto.html')