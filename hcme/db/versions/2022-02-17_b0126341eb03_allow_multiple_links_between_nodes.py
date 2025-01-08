"""Allow multiple links between nodes

Revision ID: b0126341eb03
Revises: 0eb914b8421d
Create Date: 2022-02-17 10:31:55.801949

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "b0126341eb03"
down_revision = "0eb914b8421d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("uq_links_from_to", "links", type_="unique")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        "uq_links_from_to", "links", ["from_node_id", "to_node_id"]
    )
    # ### end Alembic commands ###
