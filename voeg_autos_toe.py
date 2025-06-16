import os
import sys
from dotenv import load_dotenv

# ✅ Altijd eerst .env inladen!
load_dotenv()

# Voeg projectpad toe
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app  # Flask-app vanuit main.py
from app.database import db
from app.database.models import LuxeAuto

with app.app_context():
    autos = [
        LuxeAuto(brand="Ferrari", model="Roma", year=2023, price=350, license_plate="1-FER-001", available=True, foto_url="images/Ferrari Roma.png"),
        LuxeAuto(brand="Lamborghini", model="Urus", year=2023, price=450, license_plate="2-LAM-002", available=True, foto_url="images/Lamborghini Urus (img).png"),
        LuxeAuto(brand="Rolls-Royce", model="Ghost", year=2022, price=700, license_plate="3-RRG-003", available=True, foto_url="images/Rolls-Rolls Ghost.png"),
        LuxeAuto(brand="Bentley", model="Bentayga Hybrid", year=2023, price=550, license_plate="4-BEN-004", available=True, foto_url="images/Bentley Bentayga Hybrid.png"),
        LuxeAuto(brand="Ford", model="Mustang GT", year=2022, price=280, license_plate="5-FOR-005", available=True, foto_url="images/Ford Mustang GT.png")
    ]

    try:
        db.session.add_all(autos)
        db.session.commit()
        print("✔️ 5 luxe auto’s succesvol toegevoegd aan de database.")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Er is een fout opgetreden: {e}")

    print("📡 Database URL gebruikt:", os.getenv("DATABASE_URL"))
