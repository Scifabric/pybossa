# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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
"""This module tests the Uploader class."""

from default import Test, with_context
from pybossa.uploader.cloud_store import CloudStoreUploader
from pybossa.uploader.cloud_proxy import CloudProxyUploader
from mock import patch, PropertyMock, call, MagicMock
from werkzeug.datastructures import FileStorage
from io import StringIO


class TestCloudUploader(Test):

    conn_args = {
        'host': 's3.com',
        'headers': True
    }

    @with_context
    @patch('pybossa.uploader.cloud_store.create_connection')
    def test_cloud_uploader(self, create_connection):
        mock_conn = MagicMock()
        mock_bucket = MagicMock()
        mock_key = MagicMock()
        mock_conn.get_bucket.return_value = mock_bucket
        mock_bucket.get_key.return_value = mock_key

        create_connection.return_value = mock_conn
        u = CloudStoreUploader()
        fs = FileStorage(stream=StringIO(u'hello world'),
                         filename='the_file.jpg')

        with patch.dict(self.flask_app.config, {
                'UPLOAD_BUCKET': 'testbucket',
                'S3_UPLOAD': self.conn_args
            }):
            assert u.upload_file(fs, 'cont')

        assert u.bucket == mock_bucket
        args, kwargs = mock_key.set_contents_from_string.call_args
        assert args[0] == 'hello world'

    @with_context
    @patch('pybossa.uploader.cloud_store.create_connection')
    def test_cloud_uploader_fails(self, create_connection):
        mock_conn = MagicMock()
        mock_bucket = MagicMock()
        mock_key = MagicMock()
        mock_conn.get_bucket.return_value = mock_bucket
        mock_bucket.get_key.return_value = mock_key

        create_connection.return_value = mock_conn
        u = CloudStoreUploader()
        fs = FileStorage(stream=StringIO(u'hello world'),
                         filename='the_file.jpg')

        mock_key.set_contents_from_string.side_effect = Exception
        with patch.dict(self.flask_app.config, {'UPLOAD_BUCKET': 'testbucket'}):
            assert not u.upload_file(fs, 'cont')

    @with_context
    @patch('pybossa.uploader.cloud_store.create_connection')
    def test_cloud_uploader_delete(self, create_connection):
        mock_conn = MagicMock()
        mock_bucket = MagicMock()
        mock_conn.get_bucket.return_value = mock_bucket
        create_connection.return_value = mock_conn
        u = CloudStoreUploader()

        with patch.dict(self.flask_app.config, {
                'UPLOAD_BUCKET': 'testbucket',
                'S3_UPLOAD': self.conn_args
            }):
            assert u.delete_file('hello', 'cont')

        mock_bucket.delete_key.assert_called_with(u.key_name('cont', 'hello'))

    @with_context
    @patch('pybossa.uploader.cloud_store.create_connection')
    def test_cloud_uploader_delete_fails(self, create_connection):
        mock_conn = MagicMock()
        mock_bucket = MagicMock()
        mock_conn.get_bucket.return_value = mock_bucket
        create_connection.return_value = mock_conn
        u = CloudStoreUploader()

        mock_bucket.delete_key.side_effect = Exception
        with patch.dict(self.flask_app.config, {
                'UPLOAD_BUCKET': 'testbucket',
                'S3_UPLOAD': self.conn_args
            }):
            assert not u.delete_file('hello', 'cont')

    @with_context
    @patch('pybossa.uploader.cloud_store.create_connection')
    def test_cloud_uploader_url(self, create_connection):
        mock_conn = MagicMock()
        mock_bucket = MagicMock()
        mock_key = MagicMock()
        mock_conn.get_bucket.return_value = mock_bucket
        mock_bucket.get_key.return_value = mock_key

        create_connection.return_value = mock_conn
        rv = 'generated_url?signature=1234abcd'
        mock_key.generate_url.return_value = rv
        u = CloudStoreUploader()

        values = {
            'container': 'user_1',
            'filename': 'test.jpg'
        }
        with patch.dict(self.flask_app.config, {
                'UPLOAD_BUCKET': 'testbucket',
                'S3_UPLOAD': self.conn_args
            }):
            url = u.external_url_handler(None, None, values)
        assert url == 'generated_url', url

    @with_context
    def test_failover_url(self):
        # bucket is not configured
        u = CloudStoreUploader()

        values = {
            'container': 'user_1',
            'filename': 'test_avatar.jpg'
        }
        url = u.external_url_handler(None, None, values)
        assert url.endswith('{}/static/img/placeholder.user.png'.format(self.flask_app.config['SERVER_NAME'])), url

        values = {
            'container': 'user_1',
            'filename': 'test.jpg'
        }
        url = u.external_url_handler(None, None, values)
        assert url.endswith('{}/static/img/placeholder.project.png'.format(self.flask_app.config['SERVER_NAME'])), url


class TestCloudProxyUploader(Test):

    conn_args = {
        'host': 's3.com',
        'headers': True
    }

    @with_context
    @patch('pybossa.uploader.cloud_store.create_connection')
    def test_cloud_proxy_uploader(self, create_connection):
        mock_conn = MagicMock()
        mock_bucket = MagicMock()
        mock_key = MagicMock()
        mock_conn.get_bucket.return_value = mock_bucket
        mock_bucket.get_key.return_value = mock_key

        create_connection.return_value = mock_conn
        u = CloudProxyUploader()

        mock_key.get_contents_as_string.return_value = 'hello world'
        with patch.dict(self.flask_app.config, {
                'UPLOAD_BUCKET': 'testbucket',
                'S3_UPLOAD': self.conn_args
            }):
            response = u.send_file('test.png')
            assert response.status_code == 200
            assert response.data == 'hello world'

    @with_context
    @patch('pybossa.uploader.cloud_store.create_connection')
    def test_cloud_proxy_uploader_not_found(self, create_connection):
        mock_conn = MagicMock()
        mock_bucket = MagicMock()
        mock_key = MagicMock()
        mock_conn.get_bucket.return_value = mock_bucket
        mock_bucket.get_key.return_value = mock_key

        create_connection.return_value = mock_conn
        u = CloudProxyUploader()

        mock_key.get_contents_as_string.side_effect = Exception
        with patch.dict(self.flask_app.config, {
                'UPLOAD_BUCKET': 'testbucket',
                'S3_UPLOAD': self.conn_args
            }):
            response = u.send_file('test.png')
            assert response.status_code == 404
