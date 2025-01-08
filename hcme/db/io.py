import itertools
from abc import ABC, abstractmethod
from math import ceil
from typing import Dict, Iterable, Iterator, List

import pandas as pd
from loguru import logger
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError


def nan_to_null(df: pd.DataFrame, cols: List = []) -> pd.DataFrame:
    """Convert NaN values to None."""
    cols = cols or df.columns
    for col in cols:
        df[col] = df[col].where(df[col].notnull(), None)
    return df


def chunk(iterator: Iterator, n: int) -> Iterator:
    """Chunk an iterable into lists of at most size n."""
    iterator = iter(iterator)  # Convert whatever we have into an iterator
    for edge in iterator:  # Exit when iterator is exhausted
        boundary = itertools.islice(iterator, 0, n - 1)
        yield itertools.chain([edge], boundary)


class InvalidTransformError(Exception):
    """Transformations must always produce data."""


class Transform:
    """Syntactical sugar to create a function partial."""

    def __init__(self, func, defaults=dict()):
        self.func = func
        self.defaults = defaults

    def run(self, *args, **kwargs):
        kwargs = {**self.defaults, **kwargs}
        return self.func(*args, **kwargs)


class AbstractDataBlock(ABC):
    """Declarative loader to support transformations on some raw data source."""

    reader = staticmethod(pd.read_csv)

    reader_kwargs = {}

    # read: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.replace.html
    attribute_map = {}
    # read: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.fillna.html
    na_vals = {}

    defaults = {}

    transforms = list()

    model = None

    def __init__(self, uri, **kwargs):
        self.uri = uri

    @property
    @abstractmethod
    def header_map(self):
        """Mappings from raw data to the target model.

        Note:
            Fields not included in field mappings will be dropped.

        See: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.rename.html
        """
        pass

    def _get_transforms(self):
        for t in self.transforms:
            kwargs = {}
            if isinstance(t, str):
                func = getattr(self, t)
            else:
                func = t.func
                kwargs = t.defaults
            if not callable(func):
                msg = f"{t} must be callable."
                raise InvalidTransformError(msg)
            assert isinstance(kwargs, dict), f"Invalid transform kwargs {kwargs}"
            yield func, kwargs

    def normalize_data(self, data):
        data = data.rename(columns=self.header_map, copy=True)
        data = data.replace(to_replace=self.attribute_map)
        data = data.fillna(value=self.na_vals)
        return data

    def filter_column_names(self, df):
        if self.model:
            columns = [
                c for c in df.columns if c in self.model.__table__.columns.keys()
            ]
        else:
            columns = df.columns
        return df[columns]

    def transform_data(self, data):
        for transform, kwargs in self._get_transforms():
            logger.debug(
                f"applying transform `{{transform}}` on block {self.__class__.__name__}",
                transform=transform.__name__,
            )
            sample_data = data.sample()
            data = transform(data, **kwargs)
            if data.empty:
                raise InvalidTransformError(
                    f"Transformation {transform} produced empty data."
                )
        return data

    def clean_data(self, df):
        # Assert that anything declared in header maps exists
        for hdr in self.header_map.keys():
            assert hdr in df.columns, f"Column '{hdr}' not in {df.columns.tolist()}"
        df = df.assign(**self.defaults)
        df = self.normalize_data(df)
        df = self.transform_data(df)
        df = self.filter_column_names(df)
        return df

    def read(self, uri, **kwargs):
        """Read the source data"""
        data = self.reader(uri, **kwargs)
        return data

    def extract(self, uri, **kwargs):
        """Main entrypoint for the Block interface.

        Read data from source and apply all transform steps.
        """
        df = self.read(uri, **kwargs)
        df = self.clean_data(df)
        return df

    def parse(self, **kwargs):
        return self.extract(self.uri, **self.reader_kwargs)


class AbstractLoader(ABC):
    """Abstract loader class."""

    def __init__(
        self,
        session,
        index_elements=None,
        index_where=None,
        exclude_fields=[],
        batch_size=1000,
    ):
        self.session = session
        self.batch_size = batch_size
        self.index_elements = index_elements
        self.index_where = index_where
        self.exclude_fields = exclude_fields or list(
            set().union(self.grain, ["id", "created_at"])
        )
        self.buffer = []

    @property
    @abstractmethod
    def model(self):
        """The target model to load."""
        pass

    @property
    @abstractmethod
    def grain(self):
        """The ETL granularity of interest."""
        pass

    def stream(self, item: Dict):
        """Append an item to internal buffer"""
        self.buffer.append(item)
        if len(self.buffer) >= self.batch_size:
            self.flush()

    def flush(self):
        """Flush the internal buffer to the database."""
        if self.buffer:
            self.load(self.buffer)
        self.buffer = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.flush()

    def _make_stmt(self, buffer):
        insert_stmt = postgresql.insert(self.model.__table__).values(buffer)
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=self.index_elements or list(self.grain),
            index_where=self.index_where,
            set_={
                field: getattr(insert_stmt.excluded, field)
                for field in self.model.__table__.columns.keys()
                if (field not in self.exclude_fields and field in insert_stmt.excluded)
            },
        )
        return upsert_stmt

    def load(
        self,
        data: Iterable[Dict],
    ):
        n = 0
        for buffer in chunk(data, self.batch_size):
            buffer = list(buffer)
            n += len(buffer)
            upsert = self._make_stmt(buffer)
            self.session.execute(upsert)
            self.session.commit()
        logger.info("Loaded {n} rows to {model}", n=n, model=self.model.__tablename__)


def make_loader(model, grain):
    """Factory function for creating Loader objects on the fly."""
    return type(
        f"{model.__name__}Loader",
        (AbstractLoader,),
        {"model": model, "grain": grain},
    )
