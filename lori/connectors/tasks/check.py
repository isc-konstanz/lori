# -*- coding: utf-8 -*-
"""
lori.connectors.tasks.check
~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from typing import Optional

from lori.connectors import Database
from lori.connectors.tasks.task import ConnectorTask
from lori.typing import TimestampType


class CheckTask(ConnectorTask):
    def run(
        self,
        start: Optional[TimestampType] = None,
        end: Optional[TimestampType] = None,
    ) -> bool:
        self._logger.debug(
            f"Checking data for {len(self.channels)} channels of '{type(self.connector).__name__}': {self.connector.id}"
        )
        if isinstance(self.connector, Database):
            return self.connector.exists(self.channels, start=start, end=end)
        else:
            return False
