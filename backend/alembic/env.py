from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base

# Importing the model modules registers their tables on Base.metadata.
# Every NEW model file added in Phase 2 must be imported here too.
import app.models.user  # noqa: F401
import app.models.audit_log  # noqa: F401
import app.models.category  # noqa: F401
import app.models.complaint  # noqa: F401
import app.models.complaint_identity  # noqa: F401
import app.models.evidence  # noqa: F401
import app.models.adverse_event  # noqa: F401

config = context.config

# Use the URL from .env (via settings), not from alembic.ini.
# "%" must be doubled because alembic.ini treats it specially.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic compares this metadata with the real database to write migrations.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without connecting (rarely used)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and apply migrations."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # also detect column type changes
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()