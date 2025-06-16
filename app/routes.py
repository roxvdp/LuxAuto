import os
from flask import Blueprint, render_template, session, redirect, url_for, current_app, request
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from functools import wraps

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

@routes.route("/signup")
def signup():
    oauth_client = current_app.oauth
    return oauth_client.auth0.authorize_redirect(
        redirect_uri=url_for("routes.callback", _external=True),
        screen_hint='signup',
        prompt='login'
    )

@routes.route("/callback", methods=["GET", "POST"])
def callback():
    oauth = current_app.oauth
    token = oauth.auth0.authorize_access_token()
    userinfo = oauth.auth0.userinfo(token=token)

    session["user"] = {"userinfo": userinfo}
    email = userinfo.get("email")
    session["is_admin"] = (email == os.getenv("ADMIN_USER"))

    next_url = session.pop("next_url", None)
    return redirect(next_url or url_for("routes.index"))


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


##############
#Admin routes#
##############
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_info = session.get("user") # checken of er is ingelogd
        if not user_info:
            return redirect(url_for("routes.login", next=request.path))
        email = user_info.get("userinfo", {}).get("email")
        if email != os.getenv("ADMIN_USER"):
            return "❌ Geen toegang: je hebt geen rechten voor deze pagina te bekijken.", 403

        return f(*args, **kwargs)

    return decorated_function

@routes.route("/admin")
@admin_required
def admin():
    return render_template("admin.html")






# Terugkomst van ingelogde mensen of bezoekers
@routes.route('/')
def index():
    return render_template('index.html')

@routes.route('/profiel')
def profiel():
    if "user" not in session:
        session["next_url"] = url_for("routes.profiel")
        return redirect(url_for("routes.login"))
    return render_template('profiel.html', user=session["user"])


@routes.route('/auto')
def auto():
    return render_template('auto.html')