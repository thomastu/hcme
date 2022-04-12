import enum
from importlib import import_module

import sqlalchemy as sa
from loguru import logger
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy_utils.types import ChoiceType

from hcme.db import Base


class Metrics(Base):

    __tablename__ = "metrics"

    domain = sa.Column(sa.String(255), nullable=False)

    description = sa.Column(sa.String(255), nullable=False)

    provenance = sa.Column(sa.String(255), nullable=False)

    name = sa.Column(sa.String(255), nullable=False)

    data = sa.Column(JSON, nullable=True)

    export_hooks = sa.Column(JSONB, default=list)

    export_kwargs = sa.Column(JSONB, default=dict)

    __table_args__ = (
        sa.UniqueConstraint("domain", "name", name="uq_world_metrics_domain_name"),
    )

    def __repr__(self):
        return f"<{self.domain}:{self.name}>"
