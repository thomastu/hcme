"""update tazs to multipolygon

Revision ID: 935eb9413d58
Revises: 0089183d18be
Create Date: 2021-10-29 16:34:27.326744

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import geoalchemy2

# revision identifiers, used by Alembic.
revision = "935eb9413d58"
down_revision = "0089183d18be"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "tazs",
        "geometry",
        existing_type=geoalchemy2.types.Geometry(
            geometry_type="POLYGON",
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        ),
        type_=geoalchemy2.types.Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=False,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        ),
        nullable=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "tazs",
        "geometry",
        existing_type=geoalchemy2.types.Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=False,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        ),
        type_=geoalchemy2.types.Geometry(
            geometry_type="POLYGON",
            srid=4326,
            from_text="ST_GeomFromEWKT",
            name="geometry",
        ),
        nullable=True,
    )
    # ### end Alembic commands ###
