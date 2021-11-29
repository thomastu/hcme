import functools
from dataclasses import dataclass
from functools import cache, cached_property
from typing import List, Literal, Union
from collections import OrderedDict
import pandas as pd
import sqlalchemy as sa
from loguru import logger

from hcme import config
from hcme.db import Base, Session
from hcme.db.io import make_loader
from hcme.db.models import Metrics
from hcme.plugins import registry_factory

MetricsLoader = make_loader(
    Metrics,
    grain=[
        "name",
        "domain",
    ],
)

DEFAULT_DOMAIN = "misc"


exporters = registry_factory("hcme.exporters")


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


def export_metric(metric, hooks=[]):
    hooks = [*hooks, *metric.export_hooks]
    for hook in hooks:
        if isinstance(hook, str):
            try:
                func = exporters.get(hook)
            except ImportError:
                raise ImportError(f"Invalid export hook: {hook}")
        elif callable(hook):
            func = hook
        else:
            raise TypeError(f"Invalid export hook: {hook}")
        logger.info("Exporting Metric {self} via {hook}", self=metric, hook=hook)
        # Exports are responsible for saving their own data!
        func(metric)


def export(name=None, domain=None, default_hooks=[]):
    """Export all metrics with the given domain."""

    session = Session()
    conditions = []
    if domain:
        conditions.append(Metrics.domain == domain)
    if name:
        conditions.append(Metrics.name == name)

    where_clause = sa.and_(True, *conditions)

    query = sa.select(Metrics).where(where_clause)
    for (metric,) in session.execute(query):
        export_metric(metric, hooks=default_hooks)


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
                _data = data.to_dict(into=OrderedDict)
                recorder.record(_data, export_hooks)
            elif isinstance(data, (dict, list, tuple, float, int)):
                recorder.record(data, export_hooks)
            else:
                raise TypeError(f"{function}")
            return data

        return _wrapper

    if function:
        return _decorator(function)

    return _decorator
