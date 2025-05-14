from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = 'geheime_sleutel'  # Gebruik een veiligere sleutel in productie

    from .routes import main
    app.register_blueprint(main)

    return app
