import enum

import sqlalchemy as sa
from hcme.db import Base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils.types import ChoiceType


class Metrics(Base):

    __tablename__ = "metrics"

    domain = sa.Column(sa.String(255), nullable=False)

    description = sa.Column(sa.String(255), nullable=False)

    provenance = sa.Column(sa.String(255), nullable=False)

    name = sa.Column(sa.String(255), nullable=False)

    data = sa.Column(JSONB, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint("domain", "name", name="uq_world_metrics_domain_name"),
    )

    def __repr__(self):
        return f"<{self.domain}:{self.name} - {self.data}>"
