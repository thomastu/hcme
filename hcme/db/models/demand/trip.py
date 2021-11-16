import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.orm.relationships import foreign
from hcme.db import Base


class Trip(Base):

    __tablename__ = "trips"

    person_id = sa.Column(sa.Integer, sa.ForeignKey("persons.id"), primary_key=True)

    trip_leg = sa.Column(sa.Integer, nullable=False)

    departure = sa.Column(
        sa.Interval(native=True, second_precision=4),
        nullable=False,
    )

    origin_location_id = sa.Column(
        sa.Integer, sa.ForeignKey("locations.id"), nullable=False
    )

    destination_location_id = sa.Column(
        sa.Integer, sa.ForeignKey("locations.id"), nullable=False
    )
    # Relationship to person
    person = sa.orm.relationship("Person", back_populates="trips")

    __table_args__ = (
        sa.UniqueConstraint(
            person_id,
            trip_leg,
            name="uq_trips_person_trip_leg",
        ),
    )
