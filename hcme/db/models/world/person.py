import sqlalchemy as sa
from sqlalchemy.sql.schema import Index

from hcme.db import Base


class Person(Base):

    __tablename__ = "persons"

    id = sa.Column(sa.Integer, primary_key=True)

    age = sa.Column(sa.Integer)

    household_id = sa.Column(sa.Integer, sa.ForeignKey("households.id"))

    household = sa.orm.relationship("Household", back_populates="members")

    __table_args__ = (Index("ix_person_household_id", household_id),)
