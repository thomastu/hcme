import sqlalchemy as sa

from geoalchemy2 import Geometry
from hcme.db import Base


class Household(Base):
    """Representation of a single household."""

    __tablename__ = "households"

    location_id = sa.Column(
        sa.Integer, sa.ForeignKey("locations.id", ondelete="CASCADE")
    )

    members = sa.orm.relationship("Person", backref="household", lazy="dynamic")

    location = sa.orm.relationship("Location", backref="households", lazy="joined")
