import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# ➕ Voeg het projectpad toe zodat 'app.database.models' geïmporteerd kan worden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ✅ Importeer declarative_base vanuit je models.py
from app.database.models import Base

# 🔧 Alembic-configuratie ophalen uit alembic.ini
config = context.config

# ✅ Logging instellen via alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 🎯 Metadata van je modellen gebruiken voor autogeneratie
target_metadata = Base.metadata

def run_migrations_offline():
    """Voer migraties uit in offline-modus (zonder DB-verbinding)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Voer migraties uit in online-modus (met actieve DB-verbinding)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

# 🔁 Kies modus (offline of online)
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
