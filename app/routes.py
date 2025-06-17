import os
from flask import Blueprint, render_template, session, redirect, url_for, current_app, request, jsonify, flash
from os import environ as env
from urllib.parse import quote_plus, urlencode
from functools import wraps
from app.database.models import LuxeAuto, Usertable,ContactBericht
from app.database import db, SessionLocal

import requests
from dotenv import find_dotenv, load_dotenv

routes = Blueprint('routes', __name__)

# .env en Auth0 configuratie
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

@routes.route("/login")
def login():
    oauth = current_app.oauth
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

    # Extract relevant fields from userinfo
    auth0_user_id = userinfo.get("sub")    # Unique Auth0 user ID
    email = userinfo.get("email")
    naam = userinfo.get("name")


    # Try to find user in DB
    user = db.session.query(Usertable).filter_by(user_id=auth0_user_id).first()

    if not user:
        user = Usertable(
            user_id=auth0_user_id,
            email=email,
            naam=naam,
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

    session["user"] = {
        "userinfo": userinfo,
        "db_id": user.id,
    }
    session["is_admin"] = (email == os.getenv("ADMIN_USER"))


    next_url = session.pop("next_url", None)
    return redirect(next_url or url_for("routes.index"))

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
# Admin-only #
##############
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_info = session.get("user")
        if not user_info:
            session["next_url"] = request.path
            return redirect(url_for("routes.login"))
        email = user_info.get("userinfo", {}).get("email")
        if email != os.getenv("ADMIN_USER"):
            return "❌ Geen toegang: je hebt geen rechten voor deze pagina te bekijken.", 403
        return f(*args, **kwargs)
    return decorated_function

@routes.route("/admin")
@admin_required
def admin():
    return render_template("admin.html")


@routes.route("/admin/catalogus")
@admin_required
def catalogus_beheer():
    autos = db.session.query(LuxeAuto).all()
    return render_template("catalogus.html", autos=autos)


@routes.route('/admin/auto/toevoegen', methods=['GET', 'POST'])
@admin_required
def auto_toevoegen():
    if request.method == 'POST':
        brand = request.form.get('brand')
        model = request.form.get('model')
        year = request.form.get('year')
        price = request.form.get('price')
        license_plate = request.form.get('license_plate')
        available = bool(request.form.get('available'))
        foto_url = request.form.get('foto_url')

        nieuwe_auto = LuxeAuto(
            brand=brand,
            model=model,
            year=int(year),
            price=price,
            license_plate=license_plate,
            available=available,
            foto_url=foto_url
        )

        try:
            db.session.add(nieuwe_auto)
            db.session.commit()
            flash('Auto succesvol toegevoegd.', 'success')
            return redirect(url_for('routes.catalogus_beheer'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fout bij toevoegen: {e}', 'danger')

    return render_template("auto_toevoegen.html")

@routes.route('/admin/auto/bewerk/<int:auto_id>', methods=['GET', 'POST'])
@admin_required
def auto_bewerk(auto_id):
    auto = db.session.get(LuxeAuto, auto_id)
    if not auto:
        flash('Auto niet gevonden.', 'danger')
        return redirect(url_for('routes.catalogus_beheer'))

    if request.method == 'POST':
        auto.brand = request.form.get('brand')
        auto.model = request.form.get('model')
        auto.year = int(request.form.get('year'))
        auto.price = request.form.get('price')
        auto.license_plate = request.form.get('license_plate')
        auto.available = bool(request.form.get('available'))
        auto.foto_url = request.form.get('foto_url')

        try:
            db.session.commit()
            flash('Auto succesvol bijgewerkt.', 'success')
            return redirect(url_for('routes.catalogus_beheer'))
        except Exception as e:
            db.session.rollback()
            flash(f'Fout bij bewerken: {e}', 'danger')

    return render_template("auto_bewerken.html", auto=auto)


@routes.route('/admin/auto/verwijder/<int:auto_id>', methods=['POST'])
@admin_required
def auto_verwijder(auto_id):
    auto = db.session.get(LuxeAuto, auto_id)
    if not auto:
        flash('Auto niet gevonden.', 'danger')
        return redirect(url_for('routes.catalogus_beheer'))

    try:
        db.session.delete(auto)
        db.session.commit()
        flash('Auto succesvol verwijderd.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Fout bij verwijderen: {e}', 'danger')

    return redirect(url_for('routes.catalogus_beheer'))



#####
# API
#####
@routes.route('/sync_cars', methods=['GET'])
@admin_required
def sync_cars():
    api_url = 'https://luxury-cars-api.onrender.com/cars'
    response = requests.get(api_url)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch API data"}), 500

    cars = response.json()

    # Debug print to check foto_url before syncing
    for car_data in cars:
        print(f"Syncing car {car_data['license_plate']}: foto_url = {car_data.get('foto_url')}")

    session = db.session  # ✅ Gebruik Flask-SQLAlchemy sessie

    try:
        for car_data in cars:
            existing_car = session.query(LuxeAuto).filter_by(license_plate=car_data['license_plate']).first()
            if existing_car:
                existing_car.brand = car_data['brand']
                existing_car.model = car_data['model']
                existing_car.year = car_data['year']
                existing_car.price = car_data['price']
                existing_car.available = car_data['available']
                existing_car.foto_url = car_data.get('foto_url')
            else:
                new_car = LuxeAuto(
                    brand=car_data['brand'],
                    model=car_data['model'],
                    year=car_data['year'],
                    price=car_data['price'],
                    license_plate=car_data['license_plate'],
                    available=car_data['available'],
                    foto_url=car_data.get('foto_url')
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
# Algemeen
##########
@routes.route('/')
def index():
    return render_template('index.html')

@routes.route('/profiel')
def profiel():
    if "user" not in session:
        session["next_url"] = url_for("routes.profiel")
        return redirect(url_for("routes.login"))
    return render_template('profile.html', user=session["user"])

@routes.route("/auto")
def autos():
    beschikbare_autos = db.session.query(LuxeAuto).filter_by(available=True).all()
    return render_template("auto.html", autos=beschikbare_autos)

@routes.route('/auto/<int:auto_id>')
def auto_detail(auto_id):
    auto = db.session.query(LuxeAuto).get(auto_id)
    if not auto:
        return render_template("404.html"), 404
    return render_template("auto_detail.html", auto=auto)

@routes.route('/instellingen', methods=['GET', 'POST'])
def instellingen():
    if "user" not in session:
        session["next_url"] = url_for("routes.instellingen")
        return redirect(url_for("routes.login"))

    db_session = SessionLocal()
    gebruiker = db_session.query(Usertable).filter_by(id=session["user"]["db_id"]).first()

    if request.method == 'POST':
        gebruiker.voornaam = request.form.get('voornaam')
        gebruiker.achternaam = request.form.get('achternaam')
        gebruiker.telefoonnummer = request.form.get('telefoonnummer')
        gebruiker.adres = request.form.get('adres')
        gebruiker.email = request.form.get('email')
        db_session.commit()
        db_session.close()

        from flask import flash
        flash("Instellingen succesvol opgeslagen.", "success")
        return redirect(url_for('routes.profiel'))

    db_session.close()
    return render_template("instellingen.html", gebruiker=gebruiker)

@routes.route('/bestelgeschiedenis')
def bestelgeschiedenis():
    if "user" not in session:
        session["next_url"] = url_for("routes.bestelgeschiedenis")
        return redirect(url_for("routes.login"))
    return render_template('bestelgeschiedenis.html', user=session["user"])

@routes.route('/favorieten')
def favorieten():
    if "user" not in session:
        session["next_url"] = url_for("routes.favorieten")
        return redirect(url_for("routes.login"))
    return render_template('favorieten.html', user=session["user"])


@routes.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        naam = request.form.get("naam", "").strip()
        email = request.form.get("email", "").strip()
        onderwerp = request.form.get("onderwerp", "").strip()
        telefoon = request.form.get("telefoon", "").strip()
        bericht = request.form.get("bericht", "").strip()

        if not all([naam, email, onderwerp, bericht]):
            flash("Alle verplichte velden moeten ingevuld zijn.")
            return render_template("contact.html")

        nieuw_bericht = ContactBericht(
            naam=naam,
            email=email,
            onderwerp=onderwerp,
            telefoon=telefoon or None,
            bericht=bericht
        )
        try:
            db.session.add(nieuw_bericht)
            db.session.commit()
            return redirect(url_for("routes.contact_bevestiging"))
        except Exception as e:
            db.session.rollback()
            flash("Er is iets fout gegaan bij het verzenden van je bericht.")
            print(f"Contact fout: {e}")  # Bekijk deze fout in console/log
            return render_template("contact.html")

    return render_template("contact.html")



@routes.route("/contact/bevestiging")
def contact_bevestiging():
    return render_template("contact_bevestiging.html")