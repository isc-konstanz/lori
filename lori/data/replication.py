# -*- coding: utf-8 -*-
"""
lori.data.replicator
~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional

import tzlocal

import pandas as pd
import pytz as tz
from lori import ConfigurationException, Resource, ResourceException, Resources
from lori.connectors import Database, DatabaseException
from lori.util import floor_date, parse_freq, slice_range, to_bool, to_timedelta, to_timezone

# FIXME: Remove this once Python >= 3.9 is a requirement
try:
    from typing import Literal

except ImportError:
    from typing_extensions import Literal


class Replicator:
    SECTION: str = "replication"

    _enabled: bool = False

    database: Database

    timezone: tz.BaseTzInfo
    how: Literal["push", "pull"]
    freq: str
    full: bool
    slice: bool

    # noinspection PyShadowingNames
    @classmethod
    def build(cls, databases, resource: Resource, **kwargs) -> Replicator:
        section = resource.get(cls.SECTION, None)
        if section is None:
            section = {"database": None}
        if isinstance(section, str):
            section = {"database": section}
        elif not isinstance(section, Mapping):
            raise ConfigurationException("Invalid resource replication database: " + str(section))
        elif "database" not in section:
            section["database"] = None

        database = None
        database_id = section.pop("database")
        if database_id is not None and "." not in database_id:
            database_path = resource.id.split(".")
            for i in reversed(range(1, len(database_path))):
                _database_id = ".".join([*database_path[:i], database_id])
                if _database_id in databases.keys():
                    database = databases.get(_database_id, None)
                    break

        kwargs.update(section)
        return cls(database, **kwargs)

    # noinspection PyShadowingBuiltins
    def __init__(
        self,
        database: Optional[Database],
        timezone: Optional[tz.BaseTzInfo] = None,
        how: Literal["push", "pull"] = "push",
        freq: str = "D",
        full: bool = False,
        slice: bool = True,
        enabled: bool = True,
    ) -> None:
        self._enabled = to_bool(enabled)

        self.database = self._assert_database(database)

        if timezone is None:
            timezone = to_timezone(tzlocal.get_localzone_name())
        self.timezone = timezone

        if how not in ["push", "pull"]:
            raise ConfigurationException(f"Invalid replication method '{how}'")
        self.how = how
        self.freq = parse_freq(freq)
        self.full = to_bool(full)
        self.slice = to_bool(slice)

    @classmethod
    def _assert_database(cls, database):
        if database is None:
            return None
        if not isinstance(database, Database):
            raise ResourceException(database, f"Invalid database: {None if database is None else type(database)}")
        return database

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Replicator) and self._enabled == other._enabled and self._get_args() == other._get_args()
        )

    def __hash__(self) -> int:
        return hash((self.database, self._enabled, *self._get_args()))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.database.id})"

    def __str__(self) -> str:
        return (
            f"{type(self).__name__}:\n\tid={self.database.id}\n\t"
            + "\n\t".join(f"{k}={v}" for k, v in self._get_args().items())
            + f"\n\tenabled={self.enabled}"
        )

    # noinspection PyShadowingBuiltins
    def _get_args(self) -> Dict[str, Any]:
        return {
            "how": self.how,
            "freq": self.freq,
            "full": self.full,
            "slice": self.slice,
            "timezone": self.timezone,
        }

    @property
    def enabled(self) -> bool:
        return self._enabled and self.database is not None and self.database.is_enabled()

    # noinspection PyProtectedMember
    def replicate(self, resources: Resources) -> None:
        kwargs = self._get_args()
        how = kwargs.pop("how")

        for logger, logger_resources in resources.groupby(lambda c: c.logger._connector):
            for _, group_resources in logger_resources.groupby(lambda c: c.group):
                if how == "push":
                    replicate(logger, self.database, group_resources, **kwargs)
                elif how == "pull":
                    replicate(self.database, logger, group_resources, **kwargs)


class ReplicationException(DatabaseException):
    """
    Raise if an error occurred while replicating.

    """


# noinspection PyProtectedMember, PyUnresolvedReferences, PyTypeChecker, PyShadowingBuiltins
def replicate(
    source: Database,
    target: Database,
    resources: Resources,
    timezone: Optional[tz.BaseTzInfo] = None,
    freq: str = "D",
    full: bool = True,
    slice: bool = True,
) -> None:
    if source is None or target is None or len(resources) == 0:
        return

    logger = logging.getLogger(Replicator.__module__)
    logger.info(f"Starting to replicate data of {len(resources)} resource{'s' if len(resources) > 0 else ''}")
    target_empty = False

    if timezone is None:
        timezone = to_timezone(tzlocal.get_localzone_name())
    now = pd.Timestamp.now(tz=timezone)
    end = source.read_last_index(resources)
    if end is None:
        end = now

    start = target.read_last_index(resources) if not full else None
    if start is None:
        start = source.read_first_index(resources)
        target_empty = True
    else:
        start += pd.Timedelta(seconds=1)

    if (not any(t is None for t in [start, end]) and start >= end) or all(t is None for t in [start, end]):
        logger.debug(
            f"Skip copying values of channel{'s' if len(resources) > 1 else ''} "
            + ", ".join([f"'{r.id}'" for r in resources])
            + " without any new values found"
        )
        return

    if slice and end - start <= to_timedelta(freq):
        slice = False

    if not target_empty:
        if start > now:
            start = floor_date(now, freq=freq)

        prior = floor_date(start, timezone=timezone, freq=freq) - to_timedelta(freq)
        replicate_range(source, target, resources, prior, start)

    if slice:
        # Validate prior step, before continuing
        for slice_start, slice_end in slice_range(start, end, timezone=timezone, freq=freq):
            replicate_range(source, target, resources, slice_start, slice_end)
    else:
        replicate_range(source, target, resources, start, end)


def replicate_range(
    source: Database,
    target: Database,
    resources: Resources,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> None:
    logger = logging.getLogger(Replicator.__module__)
    logger.debug(
        f"Start copying data of channel{'s' if len(resources) > 1 else ''} "
        + ", ".join([f"'{r.id}'" for r in resources])
        + f" from {start.strftime('%d.%m.%Y (%H:%M:%S)')}"
        + f" to {end.strftime('%d.%m.%Y (%H:%M:%S)')}"
    )

    source_checksum = source.hash(resources, start, end)
    if source_checksum is None:
        logger.debug(
            f"Skipping time slice without database data for channel{'s' if len(resources) > 1 else ''} "
            + ", ".join([f"'{r.id}'" for r in resources]),
        )
        return

    target_checksum = target.hash(resources, start, end)
    if target_checksum == source_checksum:
        logger.debug(
            f"Skipping time slice without changed data for channel{'s' if len(resources) > 1 else ''} "
            + ", ".join([f"'{r.id}'" for r in resources])
        )
        return

    data = source.read(resources, start=start, end=end)
    if data is None or data.empty:  # not source.exists(resources, start=start, end=end):
        logger.debug(
            f"Skipping time slice without new data for channel{'s' if len(resources) > 1 else ''} ",
            ", ".join([f"'{r.id}'" for r in resources]),
        )
        return

    logger.info(
        f"Copying {len(data)} values of channel{'s' if len(resources) > 1 else ''} "
        + ", ".join([f"'{r.id}'" for r in resources])
        + f" from {start.strftime('%d.%m.%Y (%H:%M:%S)')}"
        + f" to {end.strftime('%d.%m.%Y (%H:%M:%S)')}"
    )

    target.write(data)
    target_checksum = target.hash(resources, start, end)
    if target_checksum != source_checksum:
        logger.error(
            f"Mismatching for {len(data)} values of channel{'s' if len(resources) > 1 else ''} "
            + ",".join([f"'{r.id}'" for r in resources])
            + f" with checksum '{source_checksum}' against target checksum '{target_checksum}'"
        )
        raise ReplicationException(target, "Checksum mismatch while synchronizing")
