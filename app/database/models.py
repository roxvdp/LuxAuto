from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, DECIMAL, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# 1️⃣ Gebruikerstabel: Ingelogde gebruikers via Auth0
class Usertable(Base):
    __tablename__ = "gebruikers"

    id = Column(Integer, primary_key=True)                          # Interne ID
    user_id = Column(String, unique=True)                           # Auth0 User ID
    email = Column(String, unique=True, nullable=False)             # Uniek e-mailadres
    name = Column(String)                                           # Volledige naam van Auth0
    voornaam = Column(String)                                       # Gebruiker voornaam
    achternaam = Column(String)                                     # Gebruiker achternaam
    telefoonnummer = Column(String)                                 # Contactnummer
    adres = Column(String)                                          # Woonadres
    taal = Column(String, default="nl")                             # Interface-taal
    darkmode = Column(String, default="False")                      # UI-thema keuze

    reservaties = relationship("Reservatie", back_populates="gebruiker", cascade="all, delete-orphan")  # Koppeling naar reservaties


# 2️⃣ Luxe auto's die verhuurd kunnen worden
class LuxeAuto(Base):
    __tablename__ = "luxe_autos"

    id = Column(Integer, primary_key=True)                          # Auto-ID
    merk = Column(String, nullable=False)                           # Merk, bv. "Audi"
    model = Column(String, nullable=False)                          # Model, bv. "Q7"
    bouwjaar = Column(Integer, nullable=False)                      # Bouwjaar, bv. 2022
    prijs_per_dag = Column(DECIMAL, nullable=False)                # Dagprijs in €
    nummerplaat = Column(String, unique=True, nullable=False)       # Unieke nummerplaat
    beschikbaar = Column(Boolean, default=True)                     # Verhuurstatus
    brandstof = Column(String)                                      # Brandstoftype: benzine/diesel/elektrisch
    transmissie = Column(String)                                    # Automaat of manueel
    foto_url = Column(String, default="img/default_car.jpg")        # Foto van de wagen

    reservaties = relationship("Reservatie", back_populates="auto") # Koppeling naar reservaties
    onderhoud = relationship("Onderhoud", back_populates="auto")    # Koppeling naar onderhoudshistoriek


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


# 5️⃣ Onderhoudshistoriek van auto's
class Onderhoud(Base):
    __tablename__ = "onderhoud"

    id = Column(Integer, primary_key=True)                          # Onderhouds-ID
    auto_id = Column(Integer, ForeignKey("luxe_autos.id"))          # Koppeling met auto
    datum = Column(DateTime, default=datetime.utcnow)               # Wanneer onderhoud gebeurde
    omschrijving = Column(String)                                   # Wat werd uitgevoerd
    kostprijs = Column(DECIMAL)                                     # Optionele kost
    voltooid = Column(Boolean, default=False)                       # Status voltooid of niet

    auto = relationship("LuxeAuto", back_populates="onderhoud")     # Relatie met de auto


# 6️⃣ Beoordelingen van auto's door klanten
class Beoordeling(Base):
    __tablename__ = "beoordelingen"

    id = Column(Integer, primary_key=True)                          # Beoordeling-ID
    auto_id = Column(Integer, ForeignKey("luxe_autos.id"))          # Gekoppelde auto
    gebruiker_id = Column(Integer, ForeignKey("gebruikers.id"))     # Gekoppelde gebruiker
    score = Column(Integer, nullable=False)                         # Score: 1–5
    commentaar = Column(Text)                                       # Vrije tekst
    datum = Column(DateTime, default=datetime.utcnow)               # Datum van beoordeling
