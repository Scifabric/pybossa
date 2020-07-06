import datetime
import pathlib
import typing as T
import uuid
from importlib import import_module
from typing import Union

import OpenSSL.crypto
import pytz

from . import types as TS


class cached_property(property):

    """A decorator that converts a function into a lazy property.
    The function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access the value:

    .. code-block:: python

        class Foo(object):
            @cached_property
            def foo(self):
                # calculate something important here
                return 42

    The class has to have a ``__dict__`` in order for this property to
    work.
    """

    # implementation detail: A subclass of python's builtin property
    # decorator, we override __get__ to check for a cached value. If one
    # chooses to invoke __get__ by hand the property will still work as
    # expected because the lookup logic is replicated in __get__ for
    # manual invocation.

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        _missing = object()
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value

    def __set__(self, instance, value):
        raise AttributeError(f"Can not set read-only attribute {type(instance).__name__}.{self.name}")

    def __delete__(self, instance):
        raise AttributeError(f"Can not delete read-only attribute {type(instance).__name__}.{self.name}")


def import_string(path: str) -> T.Any:
    """
    Import a dotted Python path to a class or other module attribute.
    ``import_string('foo.bar.MyClass')`` will return the class ``MyClass`` from
    the package ``foo.bar``.
    """
    name, attr = path.rsplit('.', 1)
    return getattr(import_module(name), attr)


def get_random_id() -> str:
    """
    Generate a random ID string. The random ID will start with the '_'
    character.
    """
    # It is very important that these random IDs NOT start with a number.
    random_id = '_' + uuid.uuid4().hex
    return random_id


def utcnow() -> datetime.datetime:
    """Get the current time in UTC, as an aware :class:`datetime.datetime`."""
    return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def certificate_to_string(certificate: TS.X509) -> str:
    """
    Take an x509 certificate and encode it to a string suitable for adding to
    XML responses.

    :param certificate: A certificate,
        perhaps loaded from :func:`certificate_from_file`.
    """
    pem_bytes = OpenSSL.crypto.dump_certificate(
        OpenSSL.crypto.FILETYPE_PEM, certificate)
    return ''.join(pem_bytes.decode('ascii').strip().split('\n')[1:-1])


def certificate_from_string(
    certificate: str,
    format=OpenSSL.crypto.FILETYPE_PEM,
) -> TS.X509:
    """
    Load an X509 certificate from a string. This just strips off the header and
    footer text.

    :param str: A certificate string.
    :param format: The format of the certificate, from :doc:`OpenSSL:api/crypto`.
    """
    return OpenSSL.crypto.load_certificate(format, certificate)


def certificate_from_file(
    filename: Union[str, pathlib.Path],
    format=OpenSSL.crypto.FILETYPE_PEM,
) -> TS.X509:
    """Load an X509 certificate from ``filename``.

    :param filename: The path to the certificate on disk.
    :param format: The format of the certificate, from :doc:`OpenSSL:api/crypto`.
    """
    with open(filename, 'r') as handle:
        return certificate_from_string(handle.read(), format)


def private_key_from_string(
    private_key: str,
    format=OpenSSL.crypto.FILETYPE_PEM,
) -> TS.PKey:
    """Load a private key from a string.

    :param str: A private key string.
    :param format: The format of the private key, from :doc:`OpenSSL:api/crypto`.
    """
    return OpenSSL.crypto.load_privatekey(format, private_key)


def private_key_from_file(
    filename: Union[str, pathlib.Path],
    format=OpenSSL.crypto.FILETYPE_PEM,
) -> TS.PKey:
    """Load a private key from ``filename``.

    :param filename: The path to the private key on disk.
    :param format: The format of the private key, from :doc:`OpenSSL:api/crypto`.
    """
    with open(filename, 'r') as handle:
        return private_key_from_string(handle.read(), format)
