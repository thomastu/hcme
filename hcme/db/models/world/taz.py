import sqlalchemy as sa
from geoalchemy2 import Geometry

from hcme.db import Base


class TAZ(Base):
    """Traffic analysis zones of interest.  A TAZ should contain multiple locations."""

    __tablename__ = "tazs"

    name = sa.Column(sa.String(255), nullable=False, unique=True)

    geometry = sa.Column(
        Geometry("MULTIPOLYGON", srid=4326, spatial_index=False), nullable=False
    )

    # Population
    # census_population = sa.Column(sa.Integer, nullable=False, default=0)

    # Reverse relationship to locations
    locations = sa.orm.relationship("Location", backref="taz")


# Spatial Index on Geometry
sa.Index("taz_geom_idx", TAZ.geometry, postgresql_using="gist")
