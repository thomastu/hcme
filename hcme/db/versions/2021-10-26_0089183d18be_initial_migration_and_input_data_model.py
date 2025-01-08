"""Initial migration and input data model

Revision ID: 0089183d18be
Revises: 9b3e5ed35ac6
Create Date: 2021-10-26 17:17:23.266103

"""
import geoalchemy2
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "0089183d18be"
down_revision = "9b3e5ed35ac6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "demand_scenarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_demand_scenarios_name"),
        "demand_scenarios",
        ["name"],
        unique=True,
    )
    op.create_table(
        "supply_scenarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_supply_scenarios_name"),
        "supply_scenarios",
        ["name"],
        unique=True,
    )
    op.create_table(
        "tazs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "taz_geom_idx",
        "tazs",
        ["geometry"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "origin",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.Column(
            "destination",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_trip_destination",
        "trips",
        ["destination"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        "idx_trip_origin",
        "trips",
        ["origin"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("demand_scenario_id", sa.Integer(), nullable=True),
        sa.Column("supply_scenario_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["demand_scenario_id"], ["demand_scenarios.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["supply_scenario_id"], ["supply_scenarios.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_experiments_name"), "experiments", ["name"], unique=True)
    op.create_table(
        "fleets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("scenario_id", sa.Integer(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("mpg", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["supply_scenarios.id"],
        ),
        sa.PrimaryKeyConstraint("id", "scenario_id"),
    )
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "coordinates",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.Column("area", sa.Float(), nullable=False),
        sa.Column("taz_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["taz_id"],
            ["tazs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "locations_coordinates_gist",
        "locations",
        ["coordinates"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_table(
        "households",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "persons",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("household_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_person_household_id", "persons", ["household_id"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_person_household_id", table_name="persons")
    op.drop_table("persons")
    op.drop_table("households")
    op.drop_index(
        "locations_coordinates_gist",
        table_name="locations",
        postgresql_using="gist",
    )
    op.drop_table("locations")
    op.drop_table("fleets")
    op.drop_index(op.f("ix_experiments_name"), table_name="experiments")
    op.drop_table("experiments")
    op.drop_index("idx_trip_origin", table_name="trips", postgresql_using="gist")
    op.drop_index("idx_trip_destination", table_name="trips", postgresql_using="gist")
    op.drop_table("trips")
    op.drop_index("taz_geom_idx", table_name="tazs", postgresql_using="gist")
    op.drop_table("tazs")
    op.drop_index(op.f("ix_supply_scenarios_name"), table_name="supply_scenarios")
    op.drop_table("supply_scenarios")
    op.drop_index(op.f("ix_demand_scenarios_name"), table_name="demand_scenarios")
    op.drop_table("demand_scenarios")
    # ### end Alembic commands ###
