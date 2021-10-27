from pathlib import Path
from dynaconf import Dynaconf, constants

_here = Path(__file__).resolve()

config = Dynaconf(
    envvar_prefix="HCME",
    load_dotenv=True,
    warn_dynaconf_global_settings=True,
    environments=True,
    default_env="hcme",
    lowercase_read=False,
    default_settings_paths=constants.DEFAULT_SETTINGS_FILES,
)


# DB URL
database_url = config.get("database_url")

# Alembic config
alembic_ini = _here.parent / "db/migrations/alembic.ini"

# Testing settings
test_settings = {"keep_db": config.get("keep_db", False)}
