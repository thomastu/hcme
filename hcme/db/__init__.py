import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from hcme.config import database_url

from .abstract import Base
from .models.registry import *

engine = sa.create_engine(database_url)

Session = sessionmaker(autocommit=False, autoflush=True, bind=engine)
