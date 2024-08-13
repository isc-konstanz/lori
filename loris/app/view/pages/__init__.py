# -*- coding: utf-8 -*-
"""
loris.app.view.pages
~~~~~~~~~~~~~~~~~~~~


"""

from .page import (  # noqa: F401
    Page,
    PageLayout,
    PageException,
    PageLayoutException,
)
from .group import PageGroup  # noqa: F401

from . import components  # noqa: F401
from .components import (  # noqa: F401
    ComponentPage,
    ComponentGroup,
)

from .header import PageHeader  # noqa: F401
from .footer import PageFooter  # noqa: F401

from .view import (  # noqa: F401
    View,
    register_component_page,
    register_component_group,
    registry,
)

from .components.system import SystemPage  # noqa: F401
from .components.weather import WeatherPage  # noqa: F401
