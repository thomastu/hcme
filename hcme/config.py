import os

from pathlib import Path
from ssl import create_default_context
from dynaconf import Dynaconf, constants

_here = Path(__file__).resolve()

_settings = Dynaconf(
    envvar_prefix="HCME",
    load_dotenv=True,
    warn_dynaconf_global_settings=True,
    environments=True,
    default_env="hcme",
    lowercase_read=True,
    default_settings_paths=constants.DEFAULT_SETTINGS_FILES,
)

create_directories = _settings.get("create_directories", False)

# DB URL
database_url = _settings.get("database_url")

# Alembic config
alembic_ini = _here.parent / "db/migrations/alembic.ini"

# Testing settings
test_settings = {"keep_db": _settings.get("keep_db", False)}

input_dir = Path(_settings.get("input_dir")).resolve(strict=not create_directories)
output_dir = Path(_settings.get("output_dir")).resolve(strict=not create_directories)

if create_directories:
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

# Registry for input files relative to data-dir
input_data = _settings.get("input_files")

# Insert a path before each key
for k, v in input_data.items():
    input_data[k] = input_dir / v

# Registry for artifacts relative to output_dir
artifacts = _settings.get("artifacts")

for k, v in artifacts.items():
    _path = output_dir / v
    if create_directories:
        if _path.is_dir():
            _path.mkdir(parents=True, exist_ok=True)
        else:
            _path.parent.mkdir(parents=True, exist_ok=True)
    artifacts[k] = _path

reference_date = _settings.get("reference_date", "2021-03-15")

beam_dir = _settings.get("beam_dir")
beam_conf = _settings.get("beam_conf")
java_exec_path = _settings.get("java_exec_path", "java")

mapbox_token = _settings.get("mapbox_token", "")
