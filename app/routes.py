import os
from flask import Blueprint, render_template, session, redirect, url_for, current_app, request, jsonify, flash
from os import environ as env
from urllib.parse import quote_plus, urlencode
from functools import wraps
from app.database.models import LuxeAuto, Usertable,ContactBericht, Reservatie
from app.database import db
from datetime import datetime, timedelta
import stripe
from app.database.models import LuxeAuto, Usertable,ContactBericht
from app.database import db, SessionLocal

import requests
from dotenv import find_dotenv, load_dotenv

routes = Blueprint('routes', __name__)

# .env en Auth0 configuratie
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
print("✅ STRIPE_SECRET_KEY uit .env:", repr(os.getenv("STRIPE_SECRET_KEY")))


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
        flash("Je bent niet ingelogd", "warning")
        return redirect(url_for("routes.login"))

    db_id = session["user"].get("db_id")
    if not db_id:
        flash("Ongeldige sessiegegevens.", "danger")
        return redirect(url_for("routes.login"))

    db_session = SessionLocal()
    gebruiker = db_session.query(Usertable).filter_by(id=db_id).first()

    return render_template("profile.html", gebruiker=gebruiker)

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

@routes.route('/auto')
def auto():
    return render_template('auto.html')

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

@routes.route("/auto/<int:auto_id>/reserveren", methods=["POST"])
def reserveer_auto(auto_id):
    if "user" not in session:
        session["next_url"] = request.path
        return redirect(url_for("routes.login"))

    db_sessie = db.session
    auto = db_sessie.query(LuxeAuto).filter_by(id=auto_id).first()
    gebruiker = db_sessie.query(Usertable).filter_by(id=session["user"]["db_id"]).first()

    if not auto or not auto.available:
        flash("Deze auto is momenteel niet beschikbaar.", "danger")
        return redirect(url_for("routes.autos"))

    try:
        start_datum = datetime.strptime(request.form["start_datum"], "%Y-%m-%d")
        eind_datum = datetime.strptime(request.form["eind_datum"], "%Y-%m-%d")
        dagen = (eind_datum - start_datum).days
        if dagen <= 0:
            flash("De gekozen datums zijn ongeldig.", "danger")
            return redirect(url_for("routes.auto_detail", auto_id=auto_id))

        totaal_prijs = float(auto.price) * dagen

        session["reservering_data"] = {
            "auto_id": auto.id,
            "start_datum": start_datum.strftime("%Y-%m-%d"),
            "eind_datum": eind_datum.strftime("%Y-%m-%d"),
            "totaal_prijs": totaal_prijs
        }

        # Stripe sessie starten
        stripe_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "unit_amount": int(totaal_prijs * 100),
                    "product_data": {
                        "name": f"{auto.brand} {auto.model} - Huur"
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.host_url + "reservering-succes",
            cancel_url=request.host_url + "reservering-annulatie",
        )

        return redirect(stripe_session.url, code=303)

    except Exception as e:
        db_sessie.rollback()
        flash("Er ging iets fout bij het starten van de betaling.", "danger")
        print(f"Stripe fout: {e}")
        return redirect(url_for("routes.auto_detail", auto_id=auto_id))

# ✅ Na betaling succesvol: reservering opslaan
@routes.route("/reservering-succes")
def reservering_succes():
    if "user" not in session or "reservering_data" not in session:
        flash("Sessie verlopen. Log opnieuw in.", "danger")
        return redirect(url_for("routes.login"))

    data = session.pop("reservering_data", None)
    db_sessie = db.session

    auto = db_sessie.query(LuxeAuto).filter_by(id=data["auto_id"]).first()
    gebruiker = db_sessie.query(Usertable).filter_by(id=session["user"]["db_id"]).first()

    if not auto or not gebruiker:
        flash("Reservatiegegevens niet gevonden.", "danger")
        return redirect(url_for("routes.autos"))

    start_datum = datetime.strptime(data["start_datum"], "%Y-%m-%d")
    eind_datum = datetime.strptime(data["eind_datum"], "%Y-%m-%d")

    nieuwe_reservatie = Reservatie(
        gebruiker_id=gebruiker.id,
        auto_id=auto.id,
        start_datum=start_datum,
        eind_datum=eind_datum,
        totaal_prijs=data["totaal_prijs"],
        status="gepland"
    )

    auto.available = False
    db_sessie.add(nieuwe_reservatie)
    db_sessie.commit()

    return render_template(
        "bedankt.html",
        data={
            "auto_id": auto.id,
            "start_datum": start_datum.strftime("%d-%m-%Y"),
            "totaal_prijs": data["totaal_prijs"]
        },
        einddatum=eind_datum.strftime("%d-%m-%Y"),
        auto=auto
    )
# ❌ Bij annulatie van betaling
@routes.route("/reservering-annulatie")
def reservering_annulatie():
    flash("Je betaling werd geannuleerd.", "warning")
    return redirect(url_for("routes.autos"))

@routes.route("/test-stripe")
def test_stripe():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "unit_amount": 1999,
                    "product_data": {"name": "Test Stripe Product"}
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=request.host_url + "reservering-succes",
            cancel_url=request.host_url + "reservering-annulatie"
        )
        return redirect(session.url, code=303)
    except Exception as e:
        print("❌ Stripe testfout:", e)
        return f"Stripe testfout: {e}"
