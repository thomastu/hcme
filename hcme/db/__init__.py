import collections
from functools import partial

import json
import orjson
import sqlalchemy as sa
from hcme.config import database_url
from sqlalchemy.orm import sessionmaker

from .abstract import Base
from .models.registry import *


def _orjson_serializer(obj):
    data = orjson.dumps(obj, option=orjson.OPT_SERIALIZE_NUMPY).decode()
    return data


engine = sa.create_engine(
    database_url,
    json_serializer=_orjson_serializer,
    json_deserializer=partial(json.loads, object_pairs_hook=collections.OrderedDict),
)

Session = sessionmaker(autocommit=False, autoflush=True, bind=engine)
