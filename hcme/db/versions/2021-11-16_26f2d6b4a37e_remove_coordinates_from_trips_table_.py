"""Remove coordinates from trips table since we have fks now

Revision ID: 26f2d6b4a37e
Revises: 3afbc980f375
Create Date: 2021-11-16 12:17:04.308639

"""
import geoalchemy2
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "26f2d6b4a37e"
down_revision = "3afbc980f375"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("idx_trip_destination", table_name="trips")
    op.drop_index("idx_trip_origin", table_name="trips")
    op.drop_column("trips", "origin")
    op.drop_column("trips", "destination")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "trips",
        sa.Column(
            "destination",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "trips",
        sa.Column(
            "origin",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.create_index("idx_trip_origin", "trips", ["origin"], unique=False)
    op.create_index(
        "idx_trip_destination", "trips", ["destination"], unique=False
    )
    # ### end Alembic commands ###
