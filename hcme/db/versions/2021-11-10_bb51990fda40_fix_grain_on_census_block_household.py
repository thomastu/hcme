"""Fix grain on census block household

Revision ID: bb51990fda40
Revises: 0fc3f732f2a8
Create Date: 2021-11-10 14:28:46.492400

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "bb51990fda40"
down_revision = "0fc3f732f2a8"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        "census_block_household_block_id",
        "census_block_household",
        ["block_id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "census_block_household_block_id",
        "census_block_household",
        type_="unique",
    )
    # ### end Alembic commands ###
