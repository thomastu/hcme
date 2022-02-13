"""Add export hook kwargs

Revision ID: 6d26d55ec855
Revises: ef08bb73a16f
Create Date: 2022-01-03 15:53:13.941663

"""
import geoalchemy2
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6d26d55ec855"
down_revision = "ef08bb73a16f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "metrics",
        sa.Column(
            "export_kwargs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("metrics", "export_kwargs")
    # ### end Alembic commands ###
