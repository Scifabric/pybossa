from lxml.etree import ElementBase
from OpenSSL.crypto import X509, PKey

__all__ = ['X509', 'PKey']

XmlNode = ElementBase  # An easier to type, and easier to import, alias
