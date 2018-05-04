# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.

from mock import patch, Mock
from default import Test, with_context
from pybossa.uploader.s3_connection import CustomConnection, CustomAuthHandler
from nose.tools import assert_raises
from boto.auth_handler import NotReadyToAuthenticate


class TestS3Connection(Test):

    @with_context
    def test_path(self):
        with patch.dict(self.flask_app.config, {'S3_HOST_SUFFIX': '/test',
                                                'S3_CUSTOM_HANDLER_HOSTS': ['s3.store.com']}):
            conn = CustomConnection(host='s3.store.com')
            path = conn.get_path(path='/')
            assert path == '/test/', path

    @with_context
    def test_path_key(self):
        with patch.dict(self.flask_app.config, {'S3_HOST_SUFFIX': '/test',
                                                'S3_CUSTOM_HANDLER_HOSTS': ['s3.store.com']}):
            conn = CustomConnection(host='s3.store.com')
            path = conn.get_path(path='/bucket/key')
            assert path == '/test/bucket/key', path

    @with_context
    def test_no_verify_context(self):
        with patch.dict(self.flask_app.config, {'S3_SSL_NO_VERIFY': True,
                                                'S3_CUSTOM_HANDLER_HOSTS': ['s3.store.com']}):
            conn = CustomConnection(host='s3.store.com', is_secure=True)
            assert 'context' in conn.http_connection_kwargs

            conn = CustomConnection(host='s3.store.com', is_secure=False)
            assert 'context' not in conn.http_connection_kwargs

    @with_context
    def test_auth_handler_error(self):
        assert_raises(NotReadyToAuthenticate, CustomAuthHandler,
                      's3.store.com', None, None)

    @with_context
    def test_custom_headers(self):
        header = 'x-custom-access-key'
        host = 's3.store.com'
        access_key = 'test-access-key'
        with patch.dict(self.flask_app.config,
                        {'S3_CUSTOM_HEADERS': [(header, 'access_key')],
                         'S3_CUSTOM_HANDLER_HOSTS': [host]}):
            conn = CustomConnection(host=host, aws_access_key_id=access_key)
            http = conn.build_base_http_request('GET', '/', None)
            http.authorize(conn)
            assert header in http.headers
            assert http.headers[header] == access_key

    @with_context
    def test_addtl_headers(self):
        header = 'x-custom-header'
        value = 'custom-header-value'
        host = 's3.store.com'
        with patch.dict(self.flask_app.config,
                        {'S3_ADDTL_HEADERS': [(header, value)],
                         'S3_CUSTOM_HANDLER_HOSTS': [host]}):
            conn = CustomConnection(host=host)
            http = conn.build_base_http_request('GET', '/', None)
            http.authorize(conn)
            assert header in http.headers
            assert http.headers[header] == value
