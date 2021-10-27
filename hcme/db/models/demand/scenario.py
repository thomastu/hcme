import sqlalchemy as sa

from sqlalchemy.orm import relationship
from hcme.db import Base


class DemandScenario(Base):

    __tablename__ = "demand_scenarios"

    name = sa.Column(sa.String(length=100), unique=True, index=True, nullable=False)

    description = sa.Column(sa.Text, nullable=True)

    experiments = relationship("Experiment", back_populates="demand_scenario")
