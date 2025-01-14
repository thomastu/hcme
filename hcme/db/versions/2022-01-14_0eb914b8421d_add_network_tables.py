"""Add network tables

Revision ID: 0eb914b8421d
Revises: 6d26d55ec855
Create Date: 2022-01-14 14:55:06.413874

"""
import geoalchemy2
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "0eb914b8421d"
down_revision = "6d26d55ec855"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "nodes",
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
        sa.Column(
            "coordinates",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "nodes_coordinates_gist",
        "nodes",
        ["coordinates"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_table(
        "links",
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
        sa.Column("from_node_id", sa.Integer(), nullable=False),
        sa.Column("to_node_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["from_node_id"],
            ["nodes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["to_node_id"],
            ["nodes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "from_node_id", "to_node_id", name="uq_links_from_to"
        ),
    )
    op.create_index(
        op.f("ix_links_from_node_id"), "links", ["from_node_id"], unique=False
    )
    op.create_index(
        op.f("ix_links_to_node_id"), "links", ["to_node_id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_links_to_node_id"), table_name="links")
    op.drop_index(op.f("ix_links_from_node_id"), table_name="links")
    op.drop_table("links")
    op.drop_index(
        "nodes_coordinates_gist", table_name="nodes", postgresql_using="gist"
    )
    op.drop_table("nodes")
    # ### end Alembic commands ###
