# -*- coding: utf-8 -*-
"""
lori
~~~~


"""

from . import _version

__version__ = _version.get_versions().get("version")
del _version


from .core import (  # noqa: F401
    Directory,
    Directories,
    Configurations,
    ConfigurationException,
    ConfigurationUnavailableException,
    Configurator,
    Context,
    Identifier,
    Resource,
    Resources,
    ResourceException,
    ResourceUnavailableException,
)

from . import converters  # noqa: F401
from .converters import (  # noqa: F401
    Converter,
    ConverterAccess,
    ConverterContext,
    ConversionException,
)

from .settings import Settings  # noqa: F401

from . import data  # noqa: F401
from .data import (  # noqa: F401
    ChannelState,
    Channel,
    Channels,
    Listener,
)

from . import connectors  # noqa: F401
from .connectors import (  # noqa: F401
    Connector,
    ConnectorException,
    ConnectionException,
    Database,
)

from .location import (  # noqa: F401
    Location,
    LocationException,
    LocationUnavailableException,
)

from .weather import (  # noqa: F401
    Weather,
    WeatherException,
    WeatherUnavailableException,
)

from . import components  # noqa: F401
from .components import (  # noqa: F401
    Component,
    ComponentException,
    ComponentUnavailableException,
)

from . import system  # noqa: F401
from .system import System  # noqa: F401

from . import io  # noqa: F401

from . import application  # noqa: F401
from .application import Application  # noqa: F401


def load(name: str = "Lori", **kwargs) -> Application:
    return Application.load(name, **kwargs)
