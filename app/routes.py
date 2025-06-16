import os
from flask import Blueprint, render_template, session, redirect, url_for, current_app, request, jsonify
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from functools import wraps
from app.database.models import LuxeAuto
from app.database import db, SessionLocal
import requests

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

#####
#API#
#####
@routes.route('/sync_cars', methods=['GET'])
@admin_required
def sync_cars():
    api_url = 'https://luxury-cars-api.onrender.com/cars'
    response = requests.get(api_url)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch API data"}), 500

    cars = response.json()
    session = SessionLocal()

    try:
        for car_data in cars:
            # Look for existing car by license_plate
            existing_car = session.query(LuxeAuto).filter_by(license_plate=car_data['license_plate']).first()
            if existing_car:
                # Update existing car fields
                existing_car.brand = car_data['brand']
                existing_car.model = car_data['model']
                existing_car.year = car_data['year']
                existing_car.price = car_data['price']
                existing_car.available = car_data['available']
                existing_car.foto_url = car_data.get('foto_url', 'img/default_car.jpg')
            else:
                # Create new car
                new_car = LuxeAuto(
                    brand=car_data['brand'],
                    model=car_data['model'],
                    year=car_data['year'],
                    price=car_data['price'],
                    license_plate=car_data['license_plate'],
                    available=car_data['available'],
                    foto_url=car_data.get('foto_url', 'img/default_car.jpg')
                )
                session.add(new_car)

        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

    return jsonify({"message": "Cars synced successfully."})


##########
#ALGEMEEN#
##########
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