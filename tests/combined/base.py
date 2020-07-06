import urllib.parse
from pathlib import Path

import attr
import flask
from flask import Flask, abort, redirect

#import flask_saml2.idp
import flask_saml2.sp
from flask_saml2.utils import certificate_from_file, private_key_from_file

KEY_DIR = Path(__file__).parent.parent / 'keys' / 'sample'

IDP_CERTIFICATE = certificate_from_file(KEY_DIR / 'idp-certificate.pem')
IDP_PRIVATE_KEY = private_key_from_file(KEY_DIR / 'idp-private-key.pem')
SP_CERTIFICATE = certificate_from_file(KEY_DIR / 'sp-certificate.pem')
SP_PRIVATE_KEY = private_key_from_file(KEY_DIR / 'sp-private-key.pem')


@attr.s
class User:
    username = attr.ib()
    email = attr.ib()


class ServiceProvider(flask_saml2.sp.ServiceProvider):

    def __init__(self, identity_providers, **kwargs):
        super().__init__(**kwargs)
        self.identity_providers = identity_providers

    def get_sp_config(self):
        return {
            'certificate': SP_CERTIFICATE,
            'private_key': SP_PRIVATE_KEY,
        }

    def get_identity_providers(self):
        return self.identity_providers


# class IdentityProvider(flask_saml2.idp.IdentityProvider):

#     login_url = 'http://idp.example.com/login/'

#     def __init__(self, service_providers, users=None, **kwargs):
#         super().__init__(**kwargs)
#         self.service_providers = service_providers
#         self.users = {}
#         if users is not None:
#             for user in users:
#                 self.add_user(user)

#     def get_idp_config(self):
#         return {
#             'autosubmit': True,
#             'certificate': IDP_CERTIFICATE,
#             'private_key': IDP_PRIVATE_KEY,
#         }

#     def add_user(self, user):
#         self.users[user.username] = user

#     def get_service_providers(self):
#         return self.service_providers

#     def login_required(self):
#         if not self.is_user_logged_in():
#             next = urllib.parse.urlencode({'next': flask.request.url})
#             abort(redirect(self.login_url + '?' + next))

#     def is_user_logged_in(self):
#         if 'user' not in flask.session:
#             return False

#         if flask.session['user'] not in self.users:
#             return False

#         return True

#     def logout(self):
#         del flask.session['user']

#     def get_current_user(self):
#         return self.users[flask.session['user']]

#     def is_valid_redirect(self, url):
#         url = urllib.parse.urlparse(url)
#         return url.scheme == 'http' and url.netloc == 'saml.serviceprovid.er'


class SamlTestCase:
    """
    Sub-classes must provide these class properties:
    IDP_CONFIG = IdentityProvider settings to use.
    """
    IDP_CONFIG = [
        {
            'CLASS': 'flask_saml2.sp.idphandler.IdPHandler',
            'OPTIONS': {
                'display_name': 'My Identity Provider',
                'entity_id': 'http://idp.example.com/saml/metadata.xml',
                'sso_url': 'http://idp.example.com/saml/login/',
                'slo_url': 'http://idp.example.com/saml/logout/',
                'certificate': IDP_CERTIFICATE,
            },
        }
    ]

    

    def create_sp_app(self, sp: flask_saml2.sp.ServiceProvider):
        app = Flask(__name__)

        app.config['SERVER_NAME'] = 'sp.example.com'
        app.debug = True
        app.testing = True

        app.secret_key = 'not a secret'

        app.register_blueprint(sp.create_blueprint(), url_prefix='/saml/')

        return app

    # def create_idp_app(self, idp: flask_saml2.idp.IdentityProvider):
    #     app = Flask(__name__)

    #     app.config['SERVER_NAME'] = 'idp.example.com'
    #     app.debug = True
    #     app.testing = True

    #     app.secret_key = 'not a secret'

    #     app.register_blueprint(idp.create_blueprint(), url_prefix='/saml/')

    #     return app

    def setup_method(self, method):
        self.sp = ServiceProvider(self.IDP_CONFIG)
        self.sp_app = self.create_sp_app(self.sp)

        self.idp = IdentityProvider(self.SP_CONFIG)
        self.idp_app = self.create_idp_app(self.idp)

        self.sp_client = self.sp_app.test_client()
        self.idp_client = self.idp_app.test_client()

    def login(self, user: User):
        if user.username not in self.idp.users:
            self.idp.add_user(user)
        with self.idp_client.session_transaction() as sess:
            sess['user'] = user.username
