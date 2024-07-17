# -*- coding: utf-8 -*-
"""
loris.data.access
~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from typing import Any, Mapping

from loris import Channel, Configurations
from loris.data import DataMapping


class DataAccess(DataMapping):
    SECTION: str = "data"

    _configured: bool = False

    # noinspection PyProtectedMember
    def __init__(self, component, context, **channels: Channel) -> None:
        super().__init__(**channels)
        self.__context = context
        self.__component = component
        if not self.__component.configs.has_section(self.SECTION):
            self.__component.configs._add_section(self.SECTION, {})

    def __repr__(self) -> str:
        return str(self.values())

    def is_configured(self) -> bool:
        return self._configured

    @property
    def configs(self):
        return self.__component.configs.get_section(self.SECTION)

    # noinspection PyProtectedMember
    def configure(self, configs: Configurations) -> None:
        if configs.has_section("connectors"):
            self.__context.connectors._do_load_sections(configs.get_section("connectors"), self.__component.uuid)

        if configs.has_section("channels"):
            self._do_load_sections(configs.get_section("channels"))

    def _do_configure(self) -> None:
        if self.is_configured():
            self._logger.warning(f"Data access of component '{self.__component.name}' already configured")
            return

        self.configure(self.configs)
        self._configured = True

    # noinspection PyProtectedMember
    def _do_load_sections(self, configs: Configurations) -> None:
        channel_defaults = self._parse_defaults(configs)
        for channel_id in [i for i in configs.keys() if i not in channel_defaults]:
            channel_configs = configs.get_section(channel_id)
            channel_configs.update(channel_defaults, replace=False)

            channel_id = channel_configs.pop("id", channel_id)
            channel_uuid = f"{self.__component.uuid}.{channel_id}"
            channel = self.__context._new(uuid=channel_uuid, id=channel_id, **channel_configs)

            # TODO: Implement channel config update
            # if channel.uuid in self:
            #     self.__get(channel.uuid).update(channel_configs)
            # else:
            #     self._add(channel)
            self._add(channel)

    # noinspection PyProtectedMember, PyUnresolvedReferences, PyShadowingBuiltins
    def add(self, id: str, **configs: Any) -> None:
        data_configs = self.configs
        if not data_configs.has_section("channels"):
            data_configs._add_section("channels", {})
        if not data_configs["channels"].has_section(id):
            data_configs["channels"]._add_section(id, configs)
        else:
            data_configs["channels"][id].update(configs, replace=False)

        if self.is_configured():
            channel_configs = self._parse_defaults(data_configs)
            # Be wary of the order. First, update the channel configs with the default configs
            # of the configuration file, then update the function arguments. Last, override
            # everything with the channel specific configurations of the file.
            channel_configs.update(configs)
            channel_configs.update(data_configs["channels"][id])
            self._add(self.__context._new(uuid=f"{self.__component.uuid}.{id}", id=id, **channel_configs))

    # noinspection PyProtectedMember
    def _add(self, channel: Channel) -> None:
        self.__context._add(channel)
        self._channels[channel.id] = channel

    @staticmethod
    def _parse_defaults(configs: Configurations) -> Mapping[str, Any]:
        return {k: v for k, v in configs.items() if not isinstance(v, Mapping) or k in ["logger", "connector"]}
