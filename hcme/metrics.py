import sqlalchemy as sa
import pandas as pd
import functools

from dataclasses import dataclass
from functools import cache, cached_property
from typing import Literal, Union, List

from hcme import config
from hcme.db import Base, Session
from hcme.db.io import make_loader
from hcme.db.models import Metrics


MetricsLoader = make_loader(
    Metrics,
    grain=[
        "name",
        "domain",
    ],
)

DEFAULT_DOMAIN = "misc"


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

    def record(self, value: Union[float, dict], export_hooks: List[str] = []):
        """Record a metric"""

        with self.loader as loader:
            loader.stream(
                {
                    "data": value,
                    "description": self.description,
                    "provenance": self.provenance,
                    "export_hooks": export_hooks,
                    **self.grain,
                }
            )


def records_to_csv(data, domain, name):
    """Export record-format JSON to a CSV."""
    out_path = config.output_dir / f"{domain}/{name}.csv"
    pd.DataFrame(data).to_csv(out_path, index=False)


def export(name=None, domain=None):
    """Export all metrics with the given domain."""

    session = Session()
    conditions = []
    if domain:
        conditions.append(Metrics.domain == domain)
    if name:
        conditions.append(Metrics.name == name)

    where_clause = sa.and_(True, *conditions)

    query = sa.select(Metrics).where(where_clause)
    for metric in session.execute(query):
        metric.export()


def metric(
    function: callable = None,
    domain: str = None,
    name: str = None,
    provenance: str = None,
    description: str = None,
    export_hooks: List[str] = [],
) -> callable:
    """
    Utiltiy to help record metrics.

    Example:

        .. code-block:: python

            @metric(domain="demand", name="OD-matrix")
            def od_matrix(self):
                ...
                # Data should be some JSON serializable format
                return data
    """
    hooks = []
    for hook in export_hooks:
        if callable(hook):
            hook = f"{hook.__module__}.{hook.__name__}"
            hooks.append(hook)
        elif isinstance(hook, str):
            hooks.append(hook)

    def _decorator(
        function,
        name=name,
        provenance=provenance,
        description=description,
        domain=domain,
        export_hooks=export_hooks,
    ):
        name = name or function.__name__
        provenance = provenance or function.__module__
        domain = domain or DEFAULT_DOMAIN
        description = description or function.__doc__
        recorder = Recorder(
            name=name, domain=domain, provenance=provenance, description=description
        )

        @functools.wraps(function)
        def _wrapper(*args, **kwargs):
            # Run the function
            data = function(*args, **kwargs)

            # Persist data and side effects
            if isinstance(data, pd.DataFrame):
                recorder.record(data.to_dict(orient="records"), export_hooks)
            elif isinstance(data, (dict, list, tuple, float, int)):
                recorder.record(data, export_hooks)
            else:
                raise TypeError(f"{function}")
            return data

        return _wrapper

    if function:
        return _decorator(function)

    return _decorator
