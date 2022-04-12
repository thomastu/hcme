"""Install postGIS

Revision ID: 9b3e5ed35ac6
Revises: 
Create Date: 2021-10-26 14:47:35.414770

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "9b3e5ed35ac6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.execute('CREATE EXTENSION IF NOT EXISTS "postgis";')


def downgrade():

    op.execute('DROP EXTENSION "postgis";')
