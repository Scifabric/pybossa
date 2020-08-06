import urllib.parse
from typing import Iterable, Optional, Tuple
from urllib.parse import urljoin

from flask import (
    Blueprint, Response, abort, current_app, redirect, render_template, request,
    session, url_for)

from flask_saml2.exceptions import CannotHandleAssertion
from flask_saml2.signing import Digester, RsaSha1Signer, Sha1Digester, Signer
from flask_saml2.types import X509, PKey
from flask_saml2.utils import certificate_to_string, import_string

from .idphandler import AuthData, IdPHandler
from .views import (
    AssertionConsumer, CannotHandleAssertionView, Login, LoginIdP, Logout,
    Metadata, SingleLogout)


class ServiceProvider:
    """
    Developers should subclass :class:`ServiceProvider`
    and provide methods to interoperate with their specific environment.
    All user interactions are performed through methods on this class.

    There are no methods that must be overridden,
    but overriding :meth:`get_default_login_return_url`
    and :meth:`get_logout_return_url` is recommended.
    """
    #: What key to store authentication details under in the session.
    session_auth_data_key = 'saml_auth_data'

    #: The name of the blueprint to generate.
    blueprint_name = 'mykaarma'

    def login_successful(
        self,
        auth_data: AuthData,
        relay_state: str,
    ) -> Response:
        """ Called when a user is successfully logged on.
        Subclasses should override this if they want to do more
        with the returned user data.
        Returns a :class:`flask.Response`,
        which is usually a redirect to :meth:`get_default_login_return_url`,
        or a redirect to the protected resource the user initially requested.
        Subclasses may override this method and return a different response,
        but they *must* call ``super()``.
        """
        self.set_auth_data_in_session(auth_data)
        return redirect(relay_state)

    # Service provider configuration

    def get_sp_config(self) -> dict:
        """
        Get the configuration for this SP.
        Defaults to ``SAML2_SP`` from :attr:`flask.Flask.config`.
        The configuration should be a dict like:

        .. code-block:: python

            {
                # The X509 certificate and private key this SP uses to
                # encrypt, validate, and sign payloads.
                'certificate': ...,
                'private_key': ...,
            }

        To load the ``certificate`` and ``private_key`` values, see

        - :func:`~.utils.certificate_from_string`
        - :func:`~.utils.certificate_from_file`
        - :func:`~.utils.private_key_from_string`
        - :func:`~.utils.private_key_from_file`
        """
        return current_app.config['SAML2_SP']

    def get_sp_entity_id(self) -> str:
        """The unique identifier for this Service Provider.
        By default, this uses the metadata URL for this SP.

        See :func:`get_metadata_url`.
        """
        return self.get_metadata_url()

    def get_sp_certificate(self) -> Optional[X509]:
        """Get the public certificate for this SP."""
        return self.get_sp_config().get('certificate')

    def get_sp_private_key(self) -> Optional[PKey]:
        """Get the private key for this SP."""
        return self.get_sp_config().get('private_key')

    def get_sp_signer(self) -> Optional[Signer]:
        """Get the signing algorithm used by this SP."""
        private_key = self.get_sp_private_key()
        if private_key is not None:
            return RsaSha1Signer(private_key)

    def get_sp_digester(self) -> Digester:
        """Get the digest algorithm used by this SP."""
        return Sha1Digester()

    def should_sign_requests(self) -> bool:
        """
        Should this SP sign its SAML statements. Defaults to True if the SP is
        configured with both a certificate and a private key.
        """
        return self.get_sp_certificate() is not None \
            and self.get_sp_private_key() is not None

    # Identity provider configuration

    def get_identity_providers(self) -> Iterable[Tuple[str, dict]]:
        """
        Get an iterable of identity provider ``config`` dicts.``config`` should
        be a dict specifying an IdPHandler subclass and optionally any
        constructor arguments:

        .. code-block:: python

            >>> list(sp.get_identity_providers())
            [{
                'CLASS': 'my_app.identity_providers.MyIdPIdPHandler',
                'OPTIONS': {
                    'entity_id': 'https://idp.example.com/metadata.xml',
                },
            }]

        Defaults to ``current_app.config['SAML2_IDENTITY_PROVIDERS']``.
        """
        return current_app.config['SAML2_IDENTITY_PROVIDERS']

    def get_login_url(self) -> str:
        """The URL of the endpoint that starts the login process.
        """
        return url_for(self.blueprint_name + '.login', _external=True, _scheme='https')

    def get_acs_url(self) -> str:
        """The URL for the Assertion Consumer Service for this SP.
        """
        return url_for(self.blueprint_name + '.acs', _external=True, _scheme='https')

    def get_sls_url(self) -> str:
        """The URL for the Single Logout Service for this SP.
        """
        return url_for(self.blueprint_name + '.sls', _external=True, _scheme='https')

    def get_metadata_url(self) -> str:
        """The URL for the metadata xml for this SP.
        """
        return url_for(self.blueprint_name + '.metadata', _external=True, _scheme='https')

    def get_default_login_return_url(self) -> Optional[str]:
        """The default URL to redirect users to once the have logged in.
        """
        return None

    def get_login_return_url(self) -> Optional[str]:
        """Get the URL to redirect the user to now that they have logged in.
        """
        urls = [
            request.args.get('next'),
            self.get_default_login_return_url(),
        ]
        for url in urls:
            if url is None:
                continue
            url = self.make_absolute_url(url)
            if self.is_valid_redirect_url(url):
                return url

        return None

    def get_logout_return_url(self) -> Optional[str]:
        """The URL to redirect users to once they have logged out.
        """
        return None

    def is_valid_redirect_url(self, url: str) -> str:
        """Is this URL valid and safe to redirect to?
        Defaults to only allowing URLs on the current server.
        """
        bits = urllib.parse.urlsplit(url)

        # Relative URLs are safe
        if not bits.scheme and not bits.netloc:
            return True

        # Otherwise the scheme and server name must match
        return bits.scheme == request.scheme \
            and bits.netloc == current_app.config['SERVER_NAME']

    # IdPHandlers

    def make_idp_handler(self, config) -> IdPHandler:
        """Construct an :class:`IdPHandler` from a config dict from
        :meth:`get_identity_providers`.
        """
        cls = import_string(config['CLASS'])
        options = config.get('OPTIONS', {})
        return cls(self, **options)

    def get_idp_handlers(self) -> Iterable[IdPHandler]:
        """Get the :class:`IdPHandler` for each service provider defined.
        """
        for config in self.get_identity_providers():
            yield self.make_idp_handler(config)

    def get_default_idp_handler(self) -> Optional[IdPHandler]:
        """Get the default IdP to sign in with.
        When logging in, if there is a default IdP,
        the user will be automatically logged in with that IdP.
        Return ``None`` if there is no default IdP.
        If there is no default, a list of IdPs to sign in with will be
        presented by the login view.
        """
        handlers = list(self.get_idp_handlers())
        if len(handlers) == 1:
            return handlers[0]
        return None

    def get_idp_handler_by_entity_id(self, entity_id) -> IdPHandler:
        """Find the :class:`IdPHandler` instance with a matching entity ID.
        """
        for handler in self.get_idp_handlers():
            if handler.entity_id == entity_id:
                return handler
        raise ValueError(f"No IdP handler with entity ID {entity_id}")

    def get_idp_handler_by_current_session(self) -> IdPHandler:
        """Get the :class:`IdPHandler` used to authenticate
        the currently logged in user.
        """
        auth_data = self.get_auth_data_in_session()
        return auth_data.handler

    # Authentication

    def login_required(self):
        """Check if a user is currently logged in to this session,
        and :meth:`flask.abort` with a redirect to the login page if not.
        It is suggested to use :meth:`is_user_logged_in`.
        """
        if not self.is_user_logged_in():
            abort(redirect(self.get_login_url()))

    def is_user_logged_in(self) -> bool:

        """Check if the user is currently logged in / authenticated with an IdP.
        """
        
        return self.session_auth_data_key in session and \
            AuthData.is_valid(self, session[self.session_auth_data_key])

    def logout(self):
        """Terminate the session for a logged in user."""
        self.clear_auth_data_in_session()

    # Misc

    def render_template(self, template: str, **context) -> str:
        """Render an HTML template.
        This method can be overridden to inject more context variables if required.
        """
        context = {'sp': self, **context}
        return render_template(template, **context)

    def set_auth_data_in_session(self, auth_data: AuthData):
        """Store authentication details from the :class:`IdPHandler`
        in the browser session.
        """
        session[self.session_auth_data_key] = auth_data.to_dict()

    def clear_auth_data_in_session(self):
        """Clear the authentication details from the session.
        This will effectively log the user out.
        """
        session.pop(self.session_auth_data_key, None)

    def get_auth_data_in_session(self) -> AuthData:
        """Get an :class:`AuthData` instance from the session data stored
        for the currently logged in user.
        """
        return AuthData.from_dict(self, session[self.session_auth_data_key])

    def make_absolute_url(self, url: str) -> str:
        """Take a local URL and make it absolute
        by prepending the current ``SERVER_NAME``.
        """
        # TODO is there a better way of doing this?
        base = '{}://{}'.format(
            request.scheme, current_app.config['SERVER_NAME'])
        return urljoin(base, url)

    def get_metadata_context(self) -> dict:
        """Get any extra context for the metadata template.
        Suggested extra context variables include 'org' and 'contacts'.
        """
        return {
            'sls_url': self.get_sls_url(),
            'acs_url': self.get_acs_url(),
            'entity_id': self.get_sp_entity_id(),
            'certificate': certificate_to_string(self.get_sp_certificate()),
            'org': None,
            'contacts': [],
        }

    def create_blueprint(self) -> Blueprint:
        """Create a Flask :class:`flask.Blueprint` for this Service Provider.
        """
        idp_bp = Blueprint(self.blueprint_name, 'mykaarma', template_folder='templates')
        idp_bp.add_url_rule('/login/', view_func=Login.as_view(
            'login_mykaarma', sp=self))
        idp_bp.add_url_rule('/login/idp/', view_func=LoginIdP.as_view(
            'login_idp', sp=self))
        idp_bp.add_url_rule('/logout/', view_func=Logout.as_view(
            'logout', sp=self))
        idp_bp.add_url_rule('/acs/', view_func=AssertionConsumer.as_view(
            'acs', sp=self),methods=['POST'])
        idp_bp.add_url_rule('/sls/', view_func=SingleLogout.as_view(
            'sls', sp=self))
        idp_bp.add_url_rule('/metadata.xml', view_func=Metadata.as_view(
            'metadata', sp=self))

        idp_bp.register_error_handler(CannotHandleAssertion, CannotHandleAssertionView.as_view(
            'cannot_handle_assertion', sp=self))

        return idp_bp
