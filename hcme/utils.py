from typing import Iterable, List
from pathlib import Path

from hcme.db import Base


def assert_depends_on(depends_on: Iterable[Path]) -> None:
    """
    Assert that each file in depends_on exists.
    """
    for f in depends_on:
        assert f.exists(), f"{f} does not exist"


def get_nullable_columns(model: Base) -> List[str]:
    """Return a list of nullable columns in a model."""
    return list(
        map(lambda c: c.name, filter(lambda c: c.nullable, model.__table__.columns))
    )
