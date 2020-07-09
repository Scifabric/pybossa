"""
The :mod:`flask_saml2.xml_parser` provides tools
for parsing XML documents from an IdP or a SP.
If the documents are signed, they will be verified as part of parsing.
"""
import logging
from typing import Iterable, Optional

import defusedxml.lxml
import lxml.etree
from signxml import XMLVerifier

from flask_saml2.types import X509, XmlNode
from flask_saml2.xml_templates import NAMESPACE_MAP


class XmlParser:
    """Parse a possibly-signed XML document.
    Subclasses must implement :meth:`is_signed`.
    """
    #: The input XML document as a string
    xml_string: str

    #: The parsed XML document
    xml_tree: XmlNode

    #: The certificate the document is signed with
    certificate: Optional[X509] = None

    def __init__(self, xml_string: str, certificate: Optional[X509]):
        """
        :param xml_string: The XML string to parse
        :param x509cert: A preshared X509 certificate to validate the signed
           XML document with
        """
        self._logger = logging.getLogger(__name__)

        if certificate is not None:
            self.certificate = certificate

        self.xml_string = xml_string
        self.xml_tree = self.parse_request(xml_string)
        if self.is_signed():
            self.xml_tree = self.parse_signed(self.xml_tree, self.certificate)

    def parse_request(self, xml_string) -> None:
        """
        Parse the SAML request.
        :raises: ValueError
        """
        try:
            return defusedxml.lxml.fromstring(xml_string)
        except lxml.etree.Error:
            message = "Could not parse request XML"
            self._logger.exception(message)
            raise ValueError(message)

    def is_signed(self):
        """Is this request signed? Looks for a ``<ds:Signature>`` element.
        Different sources will generate different signed XML documents,
        so this method must be implemented differently for each source.
        """
        raise NotImplementedError

    def parse_signed(self, xml_tree: XmlNode, certificate: X509) -> XmlNode:
        """
        Replaces all parameters with only the signed parameters. You should
        provide an x509 certificate obtained out-of-band, usually via the
        SAML metadata. Otherwise the signed data will be verified with only
        the certificate provided in the request. This is INSECURE and
        more-or-less only useful for testing.
        """
        return XMLVerifier().verify(xml_tree, x509_cert=certificate).signed_xml

    def _xpath_xml_tree(self, xpath_statement):
        return self._xpath(self.xml_tree, xpath_statement)

    def _xpath(self, base: XmlNode, xpath_statement: str) -> Iterable:
        return base.xpath(xpath_statement, namespaces=self.get_namespace_map())

    def get_namespace_map(self):
        return NAMESPACE_MAP
