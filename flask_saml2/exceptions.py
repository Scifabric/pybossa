"""
All the SAML-specific exceptions this library can throw.
"""


class SAML2Exception(Exception):
    """Base exception for all flask_saml2 exceptions."""
    pass


class MessageException(SAML2Exception):
    """An exception with a nicely formatted error message."""
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return '<{}: {}>'.format(type(self).__name__, str(self))


class CannotHandleAssertion(MessageException):
    """
    This SP or IdP handler can not handle this assertion.
    """


class UserNotAuthorized(MessageException):
    """
    User not authorized for SAML 2.0 authentication.
    """


class ImproperlyConfigured(MessageException):
    """
    Someone done goofed when configuring this application.
    """
