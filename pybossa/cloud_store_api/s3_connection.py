import boto.auth_handler
import boto.auth  # This is imported to ensure the builtin auth handlers register before us

from boto.s3.connection import S3Connection, OrdinaryCallingFormat
import ssl
from flask import current_app


class CustomConnection(S3Connection):

    def __init__(self, *args, **kwargs):
        kwargs['calling_format'] = OrdinaryCallingFormat()

        super(CustomConnection, self).__init__(*args, **kwargs)

        ssl_no_verify = current_app.config.get('S3_SSL_NO_VERIFY')
        if kwargs.get('is_secure') and ssl_no_verify:
            self.https_validate_certificates = False
            context = ssl._create_unverified_context()
            self.http_connection_kwargs['context'] = context

    def get_path(self, path='/', *args, **kwargs):
        ret = super(CustomConnection, self).get_path(path, *args, **kwargs)
        return current_app.config.get('S3_HOST_SUFFIX', '') + ret


class CustomAuthHandler(boto.auth_handler.AuthHandler):
    """Implements sending of S3's custom headers"""

    capability = ['s3']

    def __init__(self, host, config, provider):
        if host not in current_app.config.get('S3_CUSTOM_HANDLER_HOSTS', []):
            raise boto.auth_handler.NotReadyToAuthenticate()
        self._provider = provider
        boto.auth_handler.AuthHandler.__init__(self, host, config, provider)

    def add_auth(self, http_request, **kwargs):
        headers = http_request.headers
        custom_headers = current_app.config.get('S3_CUSTOM_HEADERS', [])
        addtl_headers = current_app.config.get('S3_ADDTL_HEADERS', [])
        for header, attr in custom_headers:
            headers[header] = getattr(self._provider, attr)
        for header, value in addtl_headers:
            headers[header] = value
