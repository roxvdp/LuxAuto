from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os import getenv
from dotenv import load_dotenv

# 📦 Laad .env-variabelen (zoals DATABASE_URL)
load_dotenv()

# 🌐 Haal database-URL op uit .env-bestand
DATABASE_URL = getenv("DATABASE_URL")

# 🚨 Controleer of de URL aanwezig is
if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL ontbreekt. Controleer je .env-bestand.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)