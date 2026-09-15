import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import config and metadata
from app.config import settings
from app.db.models import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name:
    fileConfig(config.config_file_name)

# Set database URL from application settings
import os
db_url = os.environ.get("DB_URL", str(settings.db_url))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Use db_url directly to avoid config parser issues
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Create engine directly from db_url to avoid config parser issues
    from sqlalchemy import create_engine
    connectable = create_engine(db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.config.get_main_option("sqlalchemy.url") is None:
    # Offline mode
    run_migrations_offline()
else:
    # Online mode
    run_migrations_online()
