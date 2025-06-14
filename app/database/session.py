from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os import getenv
from dotenv import load_dotenv
import os

# 📦 Laad .env-variabelen (zoals DATABASE_URL)
load_dotenv()

# 🌐 Haal database-URL op uit .env-bestand
DATABASE_URL = getenv("DATABASE_URL")

# 🚨 Controleer of de URL aanwezig is
if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL ontbreekt. Controleer je .env-bestand.")

# ⚙️ Maak de engine aan (verbindt met PostgreSQL)
engine = create_engine(DATABASE_URL)

# 🧪 Genereer de sessieklasse voor database-operaties
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 🛠️ Maak alle tabellen aan als ze nog niet bestaan
from app.database.models import Base  # pas aan indien models elders zit
Base.metadata.create_all(bind=engine)