# -*- coding: utf-8 -*-
"""
lori.components.camera
~~~~~~~~~~~~~~~~~~~~~~

"""

from __future__ import annotations

from lori import Configurations
from lori.components import Component, register_component_type


# noinspection SpellCheckingInspection
@register_component_type("camera")
class Camera(Component):
    def configure(self, configs: Configurations) -> None:
        super().configure(configs)

        self.data.add(
            key="frame",
            name="Frame",
            type=bytes,
            aggregation="last",
        )

    # def activate(self) -> None:
    #     super().activate()
    #     self.data.register(
    #         self._on_frame,
    #         self.data.frame,
    #         how="all",
    #         unique=False,
    #     )
    #
    # def _on_frame(self, data: pd.DataFrame) -> None:
    #     pass
