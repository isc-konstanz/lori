# -*- coding: utf-8 -*-
"""
loris.app.view.server
~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from importlib import resources
from typing import Optional

# import logging
import dash
from dash import Dash
from dash_bootstrap_components import Container, themes

from loris import Configurations
from loris.app import Application
from loris.app.server import Server, ServerMeta
from loris.app.view.pages import PageFooter, PageHeader, View


class ViewServerMeta(ServerMeta):
    # noinspection PyProtectedMember
    def __call__(cls, context: Application, configs: Configurations) -> Server:
        global _instance
        if _instance is None:
            _instance = super().__call__(context, configs)
        return _instance


# noinspection PyProtectedMember
class ViewServer(Server, Dash, metaclass=ViewServerMeta):

    def __init__(self, context: Application, configs: Configurations) -> None:
        view_path = resources.files("loris.app.view")
        super().__init__(
            name=context.name,
            title=context.name,
            context=context,
            configs=configs,
            external_stylesheets=[themes.BOOTSTRAP],
            assets_folder=str(view_path.joinpath("assets")),
            pages_folder=str(view_path.joinpath("pages")),
            use_pages=True,
            server=True,  # TODO: Probably replace this with local Flask server, to create custom REST API ?
        )
        theme = configs.get_section("theme", defaults={
            "name": context.name,
            "logo": view_path.joinpath("assets", "logo.png")
        })
        header = PageHeader(**theme)
        footer = PageFooter()

        self.view = View(context.id, header, footer)

    @property
    def context(self) -> Application:
        return super().context

    def configure(self, configs: Configurations) -> None:
        super().configure(configs)
        self._do_create_view()

    def create_view_layout(self) -> Container:
        return Container(
            id=f"{self.context.id}",
            fluid=True,
            children=[
                self.view.header.navbar,
                dash.page_container
            ],
        )

    # noinspection PyAttributeOutsideInit
    def _do_create_view(self) -> None:
        self.view._do_create_pages(self.context.components)
        self.view._do_create_layout()
        self.layout = self.create_view_layout

    def start(self) -> None:
        self.view._do_register()
        self.run()  # debug=self._logger.isEnabledFor(logging.DEBUG))


_instance: Optional[ViewServer] = None
