from pathlib import Path
from dynaconf import Dynaconf, constants

_here = Path(__file__).resolve()

_settings = Dynaconf(
    envvar_prefix="HCME",
    load_dotenv=True,
    warn_dynaconf_global_settings=True,
    environments=True,
    default_env="hcme",
    lowercase_read=False,
    default_settings_paths=constants.DEFAULT_SETTINGS_FILES,
)


# DB URL
database_url = _settings.get("database_url")

# Alembic config
alembic_ini = _here.parent / "db/migrations/alembic.ini"

# Testing settings
test_settings = {"keep_db": _settings.get("keep_db", False)}

# Data directory
input_dir = Path(_settings.get("input_dir")).resolve(strict=True)

# Output Directory
output_dir = Path(_settings.get("output_dir")).resolve(strict=True)

# Registry for input files relative to data-dir
input_data = _settings.get("input_files")

# Insert a path before each key
for k, v in input_data.items():
    input_data[k] = input_dir / v
