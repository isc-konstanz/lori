# -*- coding: utf-8 -*-
"""
    th-e-core.database
    ~~~~~~~~~~~~~~~~~~
    
    
"""
from __future__ import annotations
from abc import ABC, abstractmethod

import pytz as tz
import datetime as dt
import pandas as pd

from configparser import ConfigParser as Configurations


class Database(ABC):

    def __init__(self, enabled: str = 'true', timezone: str = 'UTC', **_) -> None:
        self.enabled = enabled.lower() == 'true'
        self.timezone = tz.timezone(timezone)

    @staticmethod
    def open(configs: Configurations, **kwargs) -> Database:
        dbargs = dict(configs.items('Database'))

        database_type = dbargs['type'].lower()
        if database_type == 'sql':
            database_tables = dict(configs.items('Tables'))
            from th_e_core.iotools.sql import SqlDatabase
            return SqlDatabase(**dbargs, **kwargs, tables=database_tables)

        elif database_type == 'csv':
            from th_e_core.iotools.csv import CsvDatabase
            return CsvDatabase(**dbargs, **kwargs)
        else:
            raise ValueError('Invalid database type argument')

    @abstractmethod
    def exists(self,
               start: pd.Timestamp | dt.datetime,
               end:   pd.Timestamp | dt.datetime = None,
               **kwargs) -> bool:
        """
        Returns if data for a specified time interval of a set of data series exists

        :param start:
            the time from which on values will be looked up for.
            For many applications, passing datetime.datetime.now() will suffice.
        :type start:
            :class:`pandas.Timestamp` or datetime

        :param end:
            the time until which values will be looked up for.
        :type end:
            :class:`pandas.Timestamp` or datetime

        :returns:
            whether values do exist in a specific time interval.
        :rtype:bool
        """
        pass

    @abstractmethod
    def read(self,
             start: pd.Timestamp | dt.datetime,
             end:   pd.Timestamp | dt.datetime = None,
             **kwargs) -> pd.DataFrame:
        """ 
        Retrieve data for a specified time interval of a set of data series
        
        :param start: 
            the time from which on values will be looked up for.
            For many applications, passing datetime.datetime.now() will suffice.
        :type start: 
            :class:`pandas.Timestamp` or datetime
        
        :param end: 
            the time until which values will be looked up for.
        :type end: 
            :class:`pandas.Timestamp` or datetime
        
        :returns: 
            the retrieved values, indexed in a specific time interval.
        :rtype: 
            :class:`pandas.DataFrame`
        """
        pass

    @abstractmethod
    def write(self, data: pd.DataFrame, **kwargs) -> None:
        """ 
        Write a set of data values, to persistently store them
        
        :param data: 
            the data set to be written
        :type data: 
            :class:`pandas.DataFrame`
        """
        pass

    def close(self, **kwargs) -> None:
        """ 
        Closes the database and cleans up all resources
        
        """
        pass


class DatabaseException(Exception):
    """
    Raise if an error occurred accessing the database.

    """
    pass