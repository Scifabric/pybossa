from typing import Mapping, Optional

from flask_saml2.types import XmlNode
from flask_saml2.utils import cached_property
from flask_saml2.xml_parser import XmlParser


class ResponseParser(XmlParser):

    def is_signed(self):
        sig = self.xml_tree.xpath('/samlp:Response/ds:Signature', namespaces=self.get_namespace_map())
        return bool(sig)

    @cached_property
    def issuer(self) -> str:
        return self._xpath_xml_tree('/samlp:Response/saml:Issuer')[0].text

    @cached_property
    def response_id(self) -> str:
        return self._xpath_xml_tree('/samlp:Response/@ID')[0]

    @cached_property
    def destination(self) -> str:
        try:
            return self._xpath_xml_tree('/samlp:Response/@Destination')[0]
        except IndexError:
            return ''

    @cached_property
    def version(self) -> str:
        return self._xpath_xml_tree('/samlp:Response/@Version')[0]

    @cached_property
    def issue_instant(self) -> str:
        return self._xpath_xml_tree('/samlp:Response/@IssueInstant')[0]

    @cached_property
    def assertion(self) -> XmlNode:
        return self._xpath_xml_tree('/samlp:Response/saml:Assertion')[0]

    @cached_property
    def subject(self) -> XmlNode:
        return self._xpath(self.assertion, 'saml:Subject')[0]

    @cached_property
    def nameid(self) -> str:
        return self._xpath(self.subject, 'saml:NameID')[0].text

    @cached_property
    def nameid_format(self) -> str:
        return self._xpath(self.subject, 'saml:NameID/@Format')[0]

    @cached_property
    def attributes(self) -> Mapping[str, str]:
        attributes = self._xpath(self.assertion, 'saml:AttributeStatement/saml:Attribute')
        return {el.get('Name'): self._xpath(el, 'saml:AttributeValue')[0].text
                for el in attributes}

    @cached_property
    def conditions(self) -> Optional[XmlNode]:
        try:
            return self._xpath(self.assertion, './saml:Conditions')[0]
        except IndexError:
            return None
