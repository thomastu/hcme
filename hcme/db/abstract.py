import sqlalchemy as sa

from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TIMESTAMP

from hcme.config import database_url


engine = sa.create_engine(database_url)

Session = sessionmaker(autocommit=False, autoflush=True, bind=engine)


class AbstractModel:

    __abstract__ = True

    id = sa.Column(sa.Integer, primary_key=True)

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
