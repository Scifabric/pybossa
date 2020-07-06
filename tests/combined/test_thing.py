import datetime

import bs4
import flask
import freezegun
import pytest
from flask import url_for

from flask_saml2.exceptions import CannotHandleAssertion
from flask_saml2.utils import utcnow

from .base import SamlTestCase, User


class TestEndToEnd(SamlTestCase):
    """
    Test the SP and IdP as a user/browser, going through the whole login
    process, following the redirects, submitting the forms, etc.
    """
    def test_end_to_end(self):
        # Pretend we want to access this protected page
        login_next = 'http://sp.example.com/dashboard'

        with self.sp_app.app_context():
            # We go here to log in
            sp_login_url = url_for('flask_saml2_sp.login', next=login_next)
            response = self.sp_client.get(sp_login_url)

            # We should be redirected to the specific IdP login URL
            sp_login_idp_url = url_for(
                'flask_saml2_sp.login_idp',
                entity_id='http://idp.example.com/saml/metadata.xml',
                next=login_next, _external=True)
            assert response.status_code == 302
            assert response.headers['Location'] == sp_login_idp_url

            # Lets fetch that...
            response = self.sp_client.get(sp_login_idp_url)

        with self.idp_app.app_context():
            # Which should send us to the IdP
            idp_login_url = response.headers['Location']
            assert idp_login_url.startswith(
                url_for('flask_saml2_idp.login_begin', _external=True))

            # Which bounces us through the hoops
            response = self.idp_client.get(idp_login_url)
            assert response.status_code == 302
            assert response.headers['Location'] \
                == url_for('flask_saml2_idp.login_process', _external=True)

            process_url = response.headers['Location']
            response = self.idp_client.get(process_url)

            # Seems we need to log in!
            assert response.status_code == 302
            assert response.headers['Location'].startswith(self.idp.login_url)

            # Lets create a user and login as them
            user = User('alex', 'alex@example.com')
            self.login(user)

            # And try the process url again
            response = self.idp_client.get(process_url)
            assert response.status_code == 200

            # It returns an HTML form that gets POSTed to the SP
            doc = bs4.BeautifulSoup(response.data, 'html.parser')
            form = doc.find(id='logged_in_post_form')
            assert form.get('method') == 'post'

            # Collect the form details...
            target = form.get('action')
            inputs = form.find_all('input')
            data = {el.get('name'): el.get('value') for el in inputs if el.get('name')}

        with self.sp_app.app_context():
            # And hit the SP as if the form was posted
            assert target == url_for('flask_saml2_sp.acs', _external=True)
            response = self.sp_client.post(target, data=data)

            # This should send us onwards to the protected page
            assert response.status_code == 302
            assert response.headers['Location'] == login_next

            ctx = self.sp_app.test_request_context('/dashboard/', environ_base={
                'HTTP_COOKIE': response.headers['Set-Cookie']})
            with ctx:
                # We should also have been logged in, horray!
                auth_data = self.sp.get_auth_data_in_session()
                assert auth_data.nameid == user.email


class TestInvalidConditions(SamlTestCase):
    user = User('alex', 'alex@example.com')

    def _make_authn_request(self):
        # Make an AuthnRequest
        idp_handler = self.sp.get_idp_handler_by_entity_id('http://idp.example.com/saml/metadata.xml')
        with self.sp_app.app_context():
            authn_request = idp_handler.get_authn_request()
            return idp_handler.encode_saml_string(authn_request.get_xml_string())

    def _process_authn_request(self, authn_request):
        with self.idp_app.app_context():
            sp_handler = next(self.idp.get_sp_handlers())

            request_handler = sp_handler.parse_authn_request(authn_request)
            with self.idp_app.test_request_context('/saml/'):
                flask.session['user'] = 'alex'
                response_xml = sp_handler.make_response(request_handler)
                return sp_handler.encode_response(response_xml)

    def _process_authn_response(self, authn_response):
        idp_handler = self.sp.get_idp_handler_by_entity_id('http://idp.example.com/saml/metadata.xml')
        with self.sp_app.app_context():
            response_handler = idp_handler.get_response_parser(authn_response)
            return idp_handler.get_auth_data(response_handler)

    def test_too_early(self):
        now = utcnow()
        self.login(self.user)

        with freezegun.freeze_time(now) as frozen:
            authn_request = self._make_authn_request()

            # step forwards a bit for transmission time
            frozen.tick(delta=datetime.timedelta(seconds=30))

            authn_response = self._process_authn_request(authn_request)

            # step backwards a bunch
            frozen.tick(delta=datetime.timedelta(minutes=-5))

            with pytest.raises(CannotHandleAssertion, match='NotBefore'):
                self._process_authn_response(authn_response)

    def test_too_late(self):
        now = utcnow()
        self.login(self.user)

        with freezegun.freeze_time(now) as frozen:
            authn_request = self._make_authn_request()

            # step forwards a bit for transmission time
            frozen.tick(delta=datetime.timedelta(seconds=30))

            authn_response = self._process_authn_request(authn_request)

            # step backwards a bunch
            frozen.tick(delta=datetime.timedelta(minutes=25))

            with pytest.raises(CannotHandleAssertion, match='NotOnOrAfter'):
                self._process_authn_response(authn_response)

    def test_just_right(self):
        now = utcnow()
        self.login(self.user)

        with freezegun.freeze_time(now) as frozen:
            authn_request = self._make_authn_request()

            # step forwards a bit for transmission time
            frozen.tick(delta=datetime.timedelta(seconds=30))

            authn_response = self._process_authn_request(authn_request)

            # step forwards a bit for transmission times
            frozen.tick(delta=datetime.timedelta(seconds=30))

            auth_data = self._process_authn_response(authn_response)
            assert auth_data.nameid == self.user.email

    def test_bad_audience(self):
        self.login(self.user)

        authn_request = self._make_authn_request()
        authn_response = self._process_authn_request(authn_request)

        # Change the server name, which will change the EntityID, which
        # will cause a mismatch in the audience.
        self.sp_app.config['SERVER_NAME'] = 'sp.sample.net'

        with pytest.raises(CannotHandleAssertion, match='AudienceRestriction'):
            self._process_authn_response(authn_response)
