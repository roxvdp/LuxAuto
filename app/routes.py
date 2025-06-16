import os
from flask import Blueprint, render_template, session, redirect, url_for, current_app, request, flash
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from functools import wraps
from app.database import db
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from app.database.models import Usertable, LuxeAuto  # Zorg ervoor dat Usertable en LuxeAuto correct geïmporteerd zijn

# Maak een blueprint
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

    session["user"] = {"userinfo": userinfo}
    email = userinfo.get("email")
    user_id = userinfo.get("sub")  # Auth0 user_id (uniek)

    session["is_admin"] = (email == os.getenv("ADMIN_USER"))

    # ⬇️ Voeg gebruiker toe als die nog niet bestaat
    gebruiker = db.session.query(Usertable).filter_by(user_id=user_id).first()
    if not gebruiker:
        nieuwe_gebruiker = Usertable(
            user_id=user_id,
            email=email,
            naam=userinfo.get("name")
        )
        db.session.add(nieuwe_gebruiker)
        db.session.commit()

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
# Admin routes#
##############
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_info = session.get("user")  # checken of er is ingelogd
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

    # Haal de gebruiker op uit de database met behulp van user_id
    user_id = session["user"]["userinfo"]["sub"]
    gebruiker = db.session.query(Usertable).filter_by(user_id=user_id).first()

    # Pass de 'gebruiker' variabele naar de template voor consistentie met profile.html
    # (Ранее здесь было 'user=session["user"]', теперь 'gebruiker=gebruiker' для соответствия шаблону)
    return render_template('profile.html', gebruiker=gebruiker)


# ========== INSTELLINGEN ==========

@routes.route('/instellingen', methods=['GET', 'POST'])  # Methoden op GET en POST gezet
def instellingen():
    if "user" not in session:
        return redirect(url_for('routes.login'))

    user_id = session["user"]["userinfo"]["sub"]
    gebruiker = db.session.query(Usertable).filter_by(user_id=user_id).first()

    if request.method == 'POST':  # Verwerk het POST verzoek van het formulier
        if gebruiker:
            gebruiker.voornaam = request.form.get("voornaam")
            gebruiker.achternaam = request.form.get("achternaam")
            gebruiker.telefoonnummer = request.form.get("telefoonnummer")
            gebruiker.adres = request.form.get("adres")
            gebruiker.email = request.form.get("email")
            db.session.commit()
            flash('Uw instellingen zijn succesvol opgeslagen!', 'success')
        else:
            # Dit zou niet moeten gebeuren als de gebruiker is ingelogd, maar voor de zekerheid
            flash('Fout: gebruiker niet gevonden.', 'danger')
        return redirect(url_for('routes.profiel'))  # Redirect na opslaan

    return render_template('instellingen.html', gebruiker=gebruiker)


# Oude update_settings route is NIET MEER NODIG, de logica zit nu in de POST van /instellingen
# DEZE REGELS ZIJN VERWIJDERD OM FOUTEN TE VOORKOMEN:
# @routes.route('/update_settings', methods=['POST'])
# def update_settings():
#    ... (deze functie is nu geintegreerd in instellingen)

# ROUTES VOOR BESTELGESCHIEDENIS EN FAVORITEN
@routes.route('/bestelgeschiedenis')
def bestelgeschiedenis():
    if "user" not in session:
        session["next_url"] = url_for("routes.bestelgeschiedenis")
        return redirect(url_for("routes.login"))
    # Haal de gebruiker op uit de database
    user_id = session["user"]["userinfo"]["sub"]
    gebruiker = db.session.query(Usertable).filter_by(user_id=user_id).first()

    # Hier kun je logica toevoegen om de bestelgeschiedenis van de gebruiker op te halen
    # Bijvoorbeeld: orders = db.session.query(OrderTable).filter_by(user_id=gebruiker.id).all()
    orders = []  # Placeholder voor echte data
    return render_template('bestelgeschiedenis.html', orders=orders)


@routes.route('/favorieten')
def favorieten():
    if "user" not in session:
        session["next_url"] = url_for("routes.favorieten")
        return redirect(url_for("routes.login"))
    # Haal de gebruiker op uit de database
    user_id = session["user"]["userinfo"]["sub"]
    gebruiker = db.session.query(Usertable).filter_by(user_id=user_id).first()

    # Hier kun je logica toevoegen om de favoriete items van de gebruiker op te halen
    # Bijvoorbeeld: favorites = db.session.query(FavoriteTable).filter_by(user_id=gebruiker.id).all()
    favorites = []  # Placeholder voor echte data
    return render_template('favorieten.html', favorites=favorites)


@routes.route('/auto', methods=['GET'])
def auto():
    locatie = request.args.get('locatie')
    start_datum = request.args.get('start_datum')
    start_tijd = request.args.get('start_tijd')
    eind_datum = request.args.get('eind_datum')
    eind_tijd = request.args.get('eind_tijd')

    # Kan filtering doen op datum en beschikbaarheid van auto's
    autos = db.session.query(LuxeAuto).filter_by(available=True).all()

    # Kleinere correctie: 'eind' variabele moet eind_datum en eind_tijd correct combineren.
    # Vooral als de vorige lijn 'eind=f"{eind_tijd} {eind_tijd}"' was, wat een typefout is.
    return render_template('auto.html', autos=autos, locatie=locatie,
                           start=f"{start_datum} {start_tijd}",
                           eind=f"{eind_datum} {eind_tijd}")