# -*- coding: utf-8 -*-
"""
lori.connectors.tasks.read
~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import inspect

import pandas as pd
from lori.connectors.tasks.task import ConnectorTask


class ReadTask(ConnectorTask):
    # noinspection PyArgumentList
    def run(self, **kwargs) -> pd.DataFrame:
        self._logger.debug(
            f"Reading {len(self.channels)} channels of '{type(self.connector).__name__}': {self.connector.id}"
        )
        signature = inspect.signature(type(self.connector).read)
        arguments = [p.name for p in signature.parameters.values() if p.kind == p.POSITIONAL_OR_KEYWORD]
        for argument in list(kwargs.keys()):
            if argument not in arguments:
                value = kwargs.pop(argument)
                self._logger.warning(
                    f"Trying to read Connector '{self.connector.id}' with unknown argument '{argument}': {value}"
                )
        return self.connector.read(self.channels, **kwargs)
