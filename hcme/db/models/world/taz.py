import sqlalchemy as sa

from geoalchemy2 import Geometry

from hcme.db import Base


class TAZ(Base):
    """Traffic analysis zones of interest.  A TAZ should contain multiple locations."""

    __tablename__ = "tazs"

    name = sa.Column(sa.String(255), nullable=False, unique=True)

    geometry = sa.Column(Geometry("POLYGON", srid=4326, spatial_index=False))


# Spatial Index on Geometry
sa.Index("taz_geom_idx", TAZ.geometry, postgresql_using="gist")
