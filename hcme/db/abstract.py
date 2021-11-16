import sqlalchemy as sa

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TIMESTAMP


class AbstractModel:

    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    created_at = sa.Column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    modified_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.utc_timestamp(),
    )

    def __repr__(self):
        return f"{self.__class__.__name__} : {self.id}"


Base = declarative_base(cls=AbstractModel)
