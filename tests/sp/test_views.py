"""
Tests for basic view functionality only.

NOTE: These classes do not test anything SAML-related.
Testing actual SAML functionality requires implementation-specific details,
which should be put in another test module.
"""
from flask import url_for
from lxml import etree

from flask_saml2.utils import certificate_to_string
from flask_saml2.xml_templates import NAMESPACE_MAP

from .base import CERTIFICATE, SamlTestCase

SAML_REQUEST = 'this is not a real SAML Request'
RELAY_STATE = 'abcdefghi0123456789'
REQUEST_DATA = {
    'SAMLRequest': SAML_REQUEST,
    'RelayState': RELAY_STATE,
}

xpath = lambda el, path: el.xpath(path, namespaces=NAMESPACE_MAP)[0]


class TestLogin(SamlTestCase):
    IDP_CONFIG = [
        {
            'CLASS': 'flask_saml2.sp.idphandler.IdPHandler',
            'OPTIONS': {
                'display_name': 'My Identity Provider',
                'entity_id': 'https://foo.idp.example.com/saml/metadata.xml',
                'sso_url': 'https://foo.idp.example.com/saml/login/',
                'slo_url': 'https://foo.idp.example.com/saml/logout/',
                'certificate': CERTIFICATE,
            },
        },
        {
            'CLASS': 'flask_saml2.sp.idphandler.IdPHandler',
            'OPTIONS': {
                'display_name': 'My Identity Provider',
                'entity_id': 'https://bar.idp.example.com/saml/metadata.xml',
                'sso_url': 'https://bar.idp.example.com/saml/login/',
                'slo_url': 'https://bar.idp.example.com/saml/logout/',
                'certificate': CERTIFICATE,
            },
        },
    ]

    def test_login(self):
        response = self.client.get(url_for('flask_saml2_sp.login'))
        foo_url = url_for(
            'flask_saml2_sp.login_idp',
            entity_id='https://foo.idp.example.com/saml/metadata.xml',
            _external=False)
        bar_url = url_for(
            'flask_saml2_sp.login_idp',
            entity_id='https://bar.idp.example.com/saml/metadata.xml',
            _external=False)

        body = response.data.decode('utf-8')
        assert foo_url in body
        assert bar_url in body

    def test_login_idp(self):
        response = self.client.get(url_for(
            'flask_saml2_sp.login_idp',
            entity_id='https://foo.idp.example.com/saml/metadata.xml'))
        assert response.status_code == 302
        assert response.headers['Location'].startswith('https://foo.idp.example.com/saml/login/')


class TestLoginSingleIdP(SamlTestCase):
    def test_login(self):
        response = self.client.get(url_for('flask_saml2_sp.login'))
        login_url = url_for(
            'flask_saml2_sp.login_idp',
            entity_id='https://idp.example.com/saml/metadata.xml',
            _external=True)
        assert response.status_code == 302
        assert response.headers['Location'] == login_url


class TestMetadataView(SamlTestCase):
    def test_rendering_metadata_view(self):
        xpath = lambda el, path: el.xpath(path, namespaces=NAMESPACE_MAP)[0]

        response = self.client.get(url_for('flask_saml2_sp.metadata'))
        response_xml = etree.fromstring(response.data.decode('utf-8'))

        certificate = certificate_to_string(CERTIFICATE)

        sp = xpath(response_xml, '/md:EntityDescriptor/md:SPSSODescriptor')
        enc_key = xpath(sp, './md:KeyDescriptor[@use="encryption"]')
        sign_key = xpath(sp, './md:KeyDescriptor[@use="signing"]')

        assert certificate == xpath(enc_key, './/ds:X509Certificate').text
        assert certificate == xpath(sign_key, './/ds:X509Certificate').text

        acs_url = url_for('flask_saml2_sp.acs', _external=True)
        slo_url = url_for('flask_saml2_sp.sls', _external=True)
        assert acs_url == xpath(sp, './md:AssertionConsumerService').attrib['Location']
        assert slo_url == xpath(sp, './md:SingleLogoutService').attrib['Location']
