from typing import Iterable
from pathlib import Path


def assert_depends_on(depends_on: Iterable[Path]) -> None:
    """
    Assert that each file in depends_on exists.
    """
    for f in depends_on:
        assert f.exists(), f"{f} does not exist"
