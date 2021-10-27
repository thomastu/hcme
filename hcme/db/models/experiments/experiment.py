import sqlalchemy as sa

from sqlalchemy.orm import relationship
from hcme.db import Base

from ..supply.scenario import SupplyScenario
from ..demand.scenario import DemandScenario


class Experiment(Base):

    __tablename__ = "experiments"

    name = sa.Column(sa.String(length=100), unique=True, index=True, nullable=False)

    demand_scenario_id = sa.Column(
        sa.Integer, sa.ForeignKey(DemandScenario.id, ondelete="CASCADE")
    )

    supply_scenario_id = sa.Column(
        sa.Integer, sa.ForeignKey(SupplyScenario.id, ondelete="CASCADE")
    )

    demand_scenario = relationship(DemandScenario, back_populates="experiments")
    supply_scenario = relationship(SupplyScenario, back_populates="experiments")
