from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, DECIMAL, Boolean, Text, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# 1️⃣ Gebruikerstabel: Ingelogde gebruikers via Auth0
class Usertable(Base):
    __tablename__ = "gebruikers"

    id = Column(Integer, primary_key=True)                          # Interne ID
    user_id = Column(String, unique=True)                           # Auth0 User ID
    email = Column(String, unique=True, nullable=False)             # Uniek e-mailadres
    naam = Column(String)                                           # Volledige naam van Auth0
    voornaam = Column(String)                                       # Gebruiker voornaam
    achternaam = Column(String)                                     # Gebruiker achternaam
    telefoonnummer = Column(String)                                 # Contactnummer
    adres = Column(String)                                          # Woonadres                     # UI-thema keuze

    reservaties = relationship("Reservatie", back_populates="gebruiker", cascade="all, delete-orphan")  # Koppeling naar reservaties


# 2️⃣ Luxe auto's die verhuurd kunnen worden
class LuxeAuto(Base):
    __tablename__ = "luxe_autos"

    id = Column(Integer, primary_key=True)                          # Auto-ID
    brand = Column(String, nullable=False)                           # Merk, bv. "Audi"
    model = Column(String, nullable=False)                             # Model, bv. "Q7"
    year = Column(Integer, nullable=False)
    price = Column(DECIMAL, nullable=False)                # Dagprijs in €
    license_plate = Column(String, unique=True, nullable=False)       # Unieke nummerplaat
    available = Column(Boolean, default=True)                     # Verhuurstatus
    foto_url = Column(String)        # Foto van de wagen

    reservaties = relationship("Reservatie", back_populates="auto") # Koppeling naar reservaties


# 3️⃣ Reservaties van auto's door gebruikers
class Reservatie(Base):
    __tablename__ = "reservaties"

    id = Column(Integer, primary_key=True)                          # Reservatie-ID
    gebruiker_id = Column(Integer, ForeignKey("gebruikers.id"), nullable=False)  # Koppeling gebruiker
    auto_id = Column(Integer, ForeignKey("luxe_autos.id"), nullable=False)       # Koppeling auto
    start_datum = Column(DateTime, nullable=False)                  # Verhuur start
    eind_datum = Column(DateTime, nullable=False)                   # Verhuur einde
    totaal_prijs = Column(DECIMAL)                                  # Totaal te betalen bedrag
    status = Column(String, default="gepland")                      # Status: gepland, geannuleerd, afgerond

    gebruiker = relationship("Usertable", back_populates="reservaties")  # Gebruikerobject
    auto = relationship("LuxeAuto", back_populates="reservaties")        # Auto-object


# 4️⃣ Contactberichten van bezoekers of klanten
class ContactBericht(Base):
    __tablename__ = "contact_berichten"

    id = Column(Integer, primary_key=True)                          # Bericht-ID
    naam = Column(String, nullable=False)                           # Naam van afzender
    email = Column(String, nullable=False)                          # E-mailadres
    telefoon = Column(String)                                       # Optioneel telefoonnummer
    onderwerp = Column(String, nullable=False)                      # Onderwerp van bericht
    bericht = Column(Text, nullable=False)                          # De inhoud van het bericht
    datum = Column(DateTime, default=datetime.utcnow)               # Tijdstip van verzending



# 5️⃣ Beoordelingen van auto's door klanten
class Beoordeling(Base):
    __tablename__ = "beoordelingen"
    __table_args__ = (
        CheckConstraint('score >= 1 AND score <= 5', name='check_score_range'),
    )

    id = Column(Integer, primary_key=True)                          # Beoordeling-ID
    auto_id = Column(Integer, ForeignKey("luxe_autos.id"),  nullable=False)          # Gekoppelde auto
    gebruiker_id = Column(Integer, ForeignKey("gebruikers.id"), nullable=False)     # Gekoppelde gebruiker
    score = Column(Integer, nullable=False)                         # Score: 1–5
    commentaar = Column(Text)                                       # Vrije tekst
    datum = Column(DateTime, default=datetime.utcnow)               # Datum van beoordeling

    gebruiker = relationship("Usertable")
    auto = relationship("LuxeAuto")
