from dataclasses import dataclass
from functools import cache, cached_property
from typing import Literal, Union

from hcme.db import Base, Session
from hcme.db.io import make_loader
from hcme.db.models import Metrics


@dataclass
class Domains:

    world: str = "world"


MetricsLoader = make_loader(
    Metrics,
    grain=[
        "name",
        "domain",
    ],
)


class Recorder:
    """Recorder class for tracking and updating calculated metrics."""

    def __init__(self, name: str, domain: str, description: str, provenance: str):
        self.grain = {
            "name": name,
            "domain": domain,
        }
        self.provenance = provenance
        self.description = description
        self.session = Session()
        self.loader = MetricsLoader(
            self.session,
            batch_size=10,
        )

    def record(self, value: Union[float, dict]):
        """Record a metric"""

        with self.loader as loader:
            loader.stream(
                {
                    "data": value,
                    "description": self.description,
                    "provenance": self.provenance,
                    **self.grain,
                }
            )
