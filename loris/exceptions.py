# -*- coding: utf-8 -*-
"""
loris.exceptions
~~~~~~~~~~~~~~~~


"""


class ResourceException(Exception):
    """
    Raise if an error occurred accessing a local resource.

    """


class ResourceUnavailableException(ResourceException):
    """
    Raise if an accessed local resource can not be found.

    """
