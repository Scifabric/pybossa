from pathlib import Path

import attr
from flask import Flask

from flask_saml2.sp import ServiceProvider
from flask_saml2.utils import certificate_from_file, private_key_from_file

KEY_DIR = Path(__file__).parent.parent / 'keys' / 'sample'
CERTIFICATE_FILE = KEY_DIR / 'sp-certificate.pem'
PRIVATE_KEY_FILE = KEY_DIR / 'sp-private-key.pem'

CERTIFICATE = certificate_from_file(CERTIFICATE_FILE)
PRIVATE_KEY = private_key_from_file(PRIVATE_KEY_FILE)


@attr.s
class User:
    username = attr.ib()
    email = attr.ib()


def create_test_app(sp: ServiceProvider):
    app = Flask(__name__)

    app.config['SERVER_NAME'] = 'sp.example.com'
    app.debug = True
    app.testing = True

    app.secret_key = 'not a secret'

    app.register_blueprint(sp.create_blueprint())

    return app


class ServiceProvider(ServiceProvider):

    def __init__(self, identity_providers, **kwargs):
        super().__init__(**kwargs)
        self.identity_providers = identity_providers

    def get_sp_config(self):
        return {
            'certificate': CERTIFICATE,
            'private_key': PRIVATE_KEY,
        }

    def get_identity_providers(self):
        return self.identity_providers


class SamlTestCase:
    """
    Sub-classes must provide these class properties:
    IDP_CONFIG = IdentityProvider settings to use.
    """
    BAD_VALUE = '!BAD VALUE!'
    USERNAME = 'fred'
    PASSWORD = 'secret'
    EMAIL = 'fred@example.com'

    IDP_CONFIG = [
        {
            'CLASS': 'flask_saml2.sp.idphandler.IdPHandler',
            'OPTIONS': {
                'display_name': 'My Identity Provider',
                'entity_id': 'https://idp.example.com/saml/metadata.xml',
                'sso_url': 'https://idp.example.com/saml/login/',
                'slo_url': 'https://idp.example.com/saml/logout/',
                'certificate': CERTIFICATE,
            },
        },
    ]

    def setup_method(self, method):
        self.sp = ServiceProvider(self.IDP_CONFIG)
        self.app = create_test_app(self.sp)
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()

    def teardown_method(self, method):
        self.context.pop()
