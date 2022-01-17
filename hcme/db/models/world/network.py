import sqlalchemy as sa

from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_MakeLine, ST_AsEWKT
from hcme.db import Base


class Node(Base):

    __tablename__ = "nodes"

    id = sa.Column(sa.Integer, primary_key=True)

    coordinates = sa.Column(
        Geometry("POINT", spatial_index=False, srid=4326), nullable=False
    )


F = sa.orm.aliased(Node)
T = sa.orm.aliased(Node)


class Link(Base):

    __tablename__ = "links"

    id = sa.Column(sa.Integer, primary_key=True)

    from_node_id = sa.Column(
        sa.Integer, sa.ForeignKey("nodes.id"), nullable=False, index=True
    )

    to_node_id = sa.Column(
        sa.Integer, sa.ForeignKey("nodes.id"), nullable=False, index=True
    )

    geometry = sa.orm.column_property(
        sa.select(ST_MakeLine(F.coordinates, T.coordinates))
        .where(from_node_id == F.id, to_node_id == T.id)
        .scalar_subquery()
    )

    __table_args__ = (
        # Unique on from and to node
        sa.UniqueConstraint(
            from_node_id,
            to_node_id,
            name="uq_links_from_to",
        ),
    )


# Manually override the spatial index to ensure alembic auto-migrations do
# not delete postGIS autogenerated indices
sa.Index("links_geometry_gist", Link.geometry, postgresql_using="gist")
sa.Index("nodes_coordinates_gist", Node.coordinates, postgresql_using="gist")