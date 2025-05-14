from flask import Flask
from flask.cli import load_dotenv

from app import create_app

app = create_app()

load_dotenv()



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

