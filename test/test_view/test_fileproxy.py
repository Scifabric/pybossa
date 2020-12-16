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


from default import with_context
import json
from helper import web
from mock import patch, MagicMock
from factories import ProjectFactory, TaskFactory, UserFactory
from pybossa.core import signer
from pybossa.encryption import AESWithGCM
from boto.exception import S3ResponseError
from pybossa.view.fileproxy import is_valid_hdfs_url


class TestFileproxy(web.Helper):

    def get_key(self, create_connection):
        key = MagicMock()
        key.content_disposition = "inline"
        bucket = MagicMock()
        bucket.get_key.return_value = key
        conn = MagicMock()
        conn.get_bucket.return_value = bucket
        create_connection.return_value = conn
        return key

    @with_context
    def test_proxy_no_signature(self):
        project = ProjectFactory.create()
        owner = project.owner

        url = '/fileproxy/encrypted/s3/test/%s/file.pdf?api_key=%s' \
             % (project.id, owner.api_key)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 403, res.status_code

    @with_context
    def test_proxy_no_task(self):
        project = ProjectFactory.create()
        owner = project.owner

        signature = signer.dumps({'task_id': 100})

        url = '/fileproxy/encrypted/s3/test/%s/file.pdf?api_key=%s&task-signature=%s' \
            % (project.id, owner.api_key, signature)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 400, res.status_code

    @with_context
    @patch('pybossa.cloud_store_api.s3.create_connection')
    def test_proxy_owner(self, create_connection):
        project = ProjectFactory.create()
        url = '/fileproxy/encrypted/s3/test/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })
        owner = project.owner

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, owner.api_key, signature)

        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        key = self.get_key(create_connection)
        key.get_contents_as_string.return_value = aes.encrypt('the content')

        with patch.dict(self.flask_app.config, {
            'FILE_ENCRYPTION_KEY': encryption_key,
            'S3_REQUEST_BUCKET': 'test'
        }):
            res = self.app.get(req_url, follow_redirects=True)
            assert res.status_code == 200, res.status_code
            assert res.data == 'the content', res.data

    @with_context
    @patch('pybossa.cloud_store_api.s3.create_connection')
    def test_proxy_admin(self, create_connection):
        admin, owner = UserFactory.create_batch(2)
        project = ProjectFactory.create(owner=owner)
        url = '/fileproxy/encrypted/s3/test/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, admin.api_key, signature)

        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        key = self.get_key(create_connection)
        key.get_contents_as_string.return_value = aes.encrypt('the content')

        with patch.dict(self.flask_app.config, {
            'FILE_ENCRYPTION_KEY': encryption_key,
            'S3_REQUEST_BUCKET': 'test'
        }):
            res = self.app.get(req_url, follow_redirects=True)
            assert res.status_code == 200, res.status_code
            assert res.data == 'the content', res.data

    @with_context
    @patch('pybossa.cloud_store_api.s3.create_connection')
    def test_file_not_in_task(self, create_connection):
        project = ProjectFactory.create()
        url = '/fileproxy/encrypted/s3/test/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': 'not/the/same'
        })
        owner = project.owner

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, owner.api_key, signature)

        res = self.app.get(req_url, follow_redirects=True)
        assert res.status_code == 403, res.status_code

    @with_context
    @patch('pybossa.cloud_store_api.s3.create_connection')
    def test_file_user(self, create_connection):
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create()
        url = '/fileproxy/encrypted/s3/test/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, user.api_key, signature)

        res = self.app.get(req_url, follow_redirects=True)
        assert res.status_code == 403, res.status_code

    @with_context
    @patch('pybossa.cloud_store_api.s3.create_connection')
    @patch('pybossa.view.fileproxy.has_lock')
    def test_file_user(self, has_lock, create_connection):
        has_lock.return_value = True
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create()
        url = '/fileproxy/encrypted/s3/test/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, user.api_key, signature)

        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        key = self.get_key(create_connection)
        key.get_contents_as_string.return_value = aes.encrypt('the content')

        with patch.dict(self.flask_app.config, {
            'FILE_ENCRYPTION_KEY': encryption_key,
            'S3_REQUEST_BUCKET': 'test'
        }):
            res = self.app.get(req_url, follow_redirects=True)
            assert res.status_code == 200, res.status_code
            assert res.data == 'the content', res.data

    @with_context
    @patch('pybossa.cloud_store_api.s3.create_connection')
    @patch('pybossa.view.fileproxy.has_lock')
    @patch('pybossa.view.fileproxy.get_secret_from_vault')
    def test_file_user_key_from_vault(self, get_secret, has_lock, create_connection):
        has_lock.return_value = True
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(info={
            'encryption': {
                'key': 'abc'
            }
        })
        url = '/fileproxy/encrypted/s3/anothertest/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, user.api_key, signature)

        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        key = self.get_key(create_connection)
        key.get_contents_as_string.return_value = aes.encrypt('the content')
        get_secret.return_value = encryption_key

        with patch.dict(self.flask_app.config, {
            'FILE_ENCRYPTION_KEY': 'another key',
            'S3_REQUEST_BUCKET': 'test',
            'ENCRYPTION_CONFIG_PATH': ['encryption']
        }):
            res = self.app.get(req_url, follow_redirects=True)
            assert res.status_code == 200, res.status_code
            assert res.data == 'the content', res.data

    @with_context
    @patch('pybossa.cloud_store_api.s3.create_connection')
    def test_proxy_s3_error(self, create_connection):
        admin, owner = UserFactory.create_batch(2)
        project = ProjectFactory.create(owner=owner)
        url = '/fileproxy/encrypted/s3/test/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, admin.api_key, signature)

        key = self.get_key(create_connection)
        key.get_contents_as_string.side_effect = S3ResponseError(403, 'Forbidden')

        res = self.app.get(req_url, follow_redirects=True)
        assert res.status_code == 500, res.status_code

    @with_context
    @patch('pybossa.cloud_store_api.s3.create_connection')
    def test_proxy_key_not_found(self, create_connection):
        admin, owner = UserFactory.create_batch(2)
        project = ProjectFactory.create(owner=owner)
        url = '/fileproxy/encrypted/s3/test/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, admin.api_key, signature)

        key = self.get_key(create_connection)
        exception = S3ResponseError(404, 'NoSuchKey')
        exception.error_code = 'NoSuchKey'
        key.get_contents_as_string.side_effect = exception

        res = self.app.get(req_url, follow_redirects=True)
        assert res.status_code == 404, res.status_code


class TestHDFSproxy(web.Helper):

    app_config = {
        'HDFS_CONFIG': {
            'test': {
                'url': 'https://webhdfs.ie',
                'user': 'testuser',
                'keytab': './oi'
            }
        },
        'VAULT_CONFIG': {
            'url': 'https://valut.com/{key_id}',
            'request': {
                'headers': {'Authorization': 'apikey'}
            },
            'response': ['key'],
            'error': ['error']
        },
        'ENCRYPTION_CONFIG_PATH': ['ext_config', 'encryption']
    }

    @with_context
    def test_proxy_no_config(self):
        project = ProjectFactory.create()
        owner = project.owner

        url = '/fileproxy/hdfs/test/%s/file.pdf?api_key=%s' \
             % (project.id, owner.api_key)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

    @with_context
    def test_proxy_no_signature(self):
        project = ProjectFactory.create()
        owner = project.owner

        url = '/fileproxy/hdfs/test/%s/file.pdf?api_key=%s' \
             % (project.id, owner.api_key)
        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(url, follow_redirects=True)
            assert res.status_code == 403, res.status_code

    @with_context
    def test_proxy_no_task(self):
        project = ProjectFactory.create()
        owner = project.owner

        signature = signer.dumps({'task_id': 100})

        url = '/fileproxy/hdfs/test/%s/file.pdf?api_key=%s&task-signature=%s' \
            % (project.id, owner.api_key, signature)
        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(url, follow_redirects=True)
            assert res.status_code == 400, res.status_code

    @with_context
    @patch('pybossa.view.fileproxy.HDFSKerberos.get')
    @patch('pybossa.view.fileproxy.requests.get')
    def test_proxy_owner(self, http_get, hdfs_get):
        res = MagicMock()
        res.json.return_value = {'key': 'testkey'}
        http_get.return_value = res

        project = ProjectFactory.create(info={
            'ext_config': {
                'encryption': {'key_id': 123}
            }
        })
        url = '/fileproxy/hdfs/test/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })
        owner = project.owner

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, owner.api_key, signature)

        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        hdfs_get.return_value = aes.encrypt('the content')

        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(req_url, follow_redirects=True)
            assert res.status_code == 200, res.status_code
            assert res.data == 'the content', res.data

    @with_context
    @patch('pybossa.view.fileproxy.HDFSKerberos.get')
    @patch('pybossa.view.fileproxy.requests.get')
    def test_proxy_admin(self, http_get, hdfs_get):
        res = MagicMock()
        res.json.return_value = {'key': 'testkey'}
        http_get.return_value = res

        admin, owner = UserFactory.create_batch(2)
        project = ProjectFactory.create(owner=owner, info={
            'ext_config': {
                'encryption': {'key_id': 123}
            }
        })
        url = '/fileproxy/hdfs/test/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, admin.api_key, signature)

        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        hdfs_get.return_value = aes.encrypt('the content')

        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(req_url, follow_redirects=True)
            assert res.status_code == 200, res.status_code
            assert res.data == 'the content', res.data

    @with_context
    @patch('pybossa.view.fileproxy.HDFSKerberos.get')
    @patch('pybossa.view.fileproxy.requests.get')
    def test_proxy_key_err(self, http_get, hdfs_get):
        res = MagicMock()
        res.json.return_value = {'error': 'an error occurred'}
        http_get.return_value = res

        admin, owner = UserFactory.create_batch(2)
        project = ProjectFactory.create(owner=owner, info={
            'ext_config': {
                'encryption': {'key_id': 123}
            }
        })
        url = '/fileproxy/hdfs/test/%s/file.pdf' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s?api_key=%s&task-signature=%s' % (url, admin.api_key, signature)

        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(req_url, follow_redirects=True)
            assert res.status_code == 500, res.status_code

    @with_context
    @patch('pybossa.view.fileproxy.HDFSKerberos.get')
    @patch('pybossa.view.fileproxy.requests.get')
    def test_offset_length(self, http_get, hdfs_get):
        res = MagicMock()
        res.json.return_value = {'key': 'testkey'}
        http_get.return_value = res

        project = ProjectFactory.create(info={
            'ext_config': {
                'encryption': {'key_id': 123}
            }
        })
        url = '/fileproxy/hdfs/test/%s/file.ndjson?offset=10&length=10' % project.id
        task = TaskFactory.create(project=project, info={
            'url': url
        })
        owner = project.owner

        signature = signer.dumps({'task_id': task.id})
        req_url = '%s&api_key=%s&task-signature=%s' % (url, owner.api_key, signature)

        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        hdfs_get.return_value = aes.encrypt('the content')

        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(req_url, follow_redirects=True)
            assert res.status_code == 200, res.status_code
            assert res.data == 'the content', res.data


def test_is_file_url():
    file_url = '/a/b'
    qps = {'offset': ['1'], 'length': ['2']}
    is_valid_url = is_valid_hdfs_url(file_url, qps)
    assert not is_valid_url(1)
    assert not is_valid_url('/a/c')
    assert not is_valid_url('/a/b?offset=1')
    assert not is_valid_url('/a/b?offset=1&offset=2')
    assert not is_valid_url('/a/b?length=2')
    assert not is_valid_url('/a/b?offset=1&length=3')
    assert not is_valid_url('/a/b?offset=1&length=3&task-signature=asdfasdfad')
    assert is_valid_url('/a/b?offset=1&length=2')
    assert is_valid_url('/a/b?offset=1&length=2&task-signature=asdfasdfas')


class TestEncryptedPayload(web.Helper):

    app_config = {
        'VAULT_CONFIG': {
            'url': 'https://valut.com/{key_id}',
            'request': {
                'headers': {'Authorization': 'apikey'}
            },
            'response': ['key'],
            'error': ['error']
        },
        'ENCRYPTION_CONFIG_PATH': ['ext_config', 'encryption']
    }

    @with_context
    def test_proxy_no_signature(self):
        project = ProjectFactory.create()
        owner = project.owner

        task_id = 2020127
        url = '/fileproxy/encrypted/taskpayload/%s/%s?api_key=%s' \
             % (project.id, task_id, owner.api_key)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 403, res.status_code

    @with_context
    def test_proxy_no_task(self):
        project = ProjectFactory.create()
        owner = project.owner

        task_id = 2020127
        signature = signer.dumps({'task_id': task_id})

        url = '/fileproxy/encrypted/taskpayload/%s/%s?api_key=%s&task-signature=%s' \
            % (project.id, task_id, owner.api_key, signature)
        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(url, follow_redirects=True)
            assert res.status_code == 400, res.status_code

    @with_context
    @patch('pybossa.view.fileproxy.requests.get')
    def test_proxy_owner(self, http_get):
        res = MagicMock()
        res.json.return_value = {'key': 'testkey'}
        http_get.return_value = res

        project = ProjectFactory.create(info={
            'ext_config': {
                'encryption': {'key_id': 123}
            }
        })

        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        content = json.dumps(dict(a=1,b="2"))
        encrypted_content = aes.encrypt(content)
        task = TaskFactory.create(project=project, info={
            'private_json__encrypted_payload': encrypted_content
        })
        owner = project.owner

        signature = signer.dumps({'task_id': task.id})
        url = '/fileproxy/encrypted/taskpayload/%s/%s?api_key=%s&task-signature=%s' \
            % (project.id, task.id, owner.api_key, signature)

        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(url, follow_redirects=True)
            assert res.status_code == 200, res.status_code
            assert res.data == content, res.data

    @with_context
    @patch('pybossa.view.fileproxy.requests.get')
    def test_proxy_admin(self, http_get):
        res = MagicMock()
        res.json.return_value = {'key': 'testkey'}
        http_get.return_value = res

        admin, owner = UserFactory.create_batch(2)
        project = ProjectFactory.create(owner=owner, info={
            'ext_config': {
                'encryption': {'key_id': 123}
            }
        })

        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        content = json.dumps(dict(a=1,b="2"))
        encrypted_content = aes.encrypt(content)
        task = TaskFactory.create(project=project, info={
            'private_json__encrypted_payload': encrypted_content
        })

        signature = signer.dumps({'task_id': task.id})
        url = '/fileproxy/encrypted/taskpayload/%s/%s?api_key=%s&task-signature=%s' \
            % (project.id, task.id, admin.api_key, signature)

        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(url, follow_redirects=True)
            assert res.status_code == 200, res.status_code
            assert res.data == content, res.data

    @with_context
    @patch('pybossa.view.fileproxy.requests.get')
    def test_empty_response(self, http_get):
        """Returns empty response with task payload not containing encrypted data."""
        res = MagicMock()
        res.json.return_value = {'key': 'testkey'}
        http_get.return_value = res

        project = ProjectFactory.create(info={
            'ext_config': {
                'encryption': {'key_id': 123}
            }
        })
        encryption_key = 'testkey'
        task = TaskFactory.create(project=project, info={}) # missing private_json__encrypted_payload
        owner = project.owner

        signature = signer.dumps({'task_id': task.id})
        url = '/fileproxy/encrypted/taskpayload/%s/%s?api_key=%s&task-signature=%s' \
            % (project.id, task.id, owner.api_key, signature)

        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(url, follow_redirects=True)
            assert res.status_code == 200, res.status_code
            assert res.data == '', res.data

    @with_context
    @patch('pybossa.view.fileproxy.requests.get')
    def test_proxy_key_err(self, http_get):
        res = MagicMock()
        res.json.return_value = {'error': 'an error occurred'}
        http_get.return_value = res

        admin, owner = UserFactory.create_batch(2)
        project = ProjectFactory.create(owner=owner, info={
            'ext_config': {
                'encryption': {'key_id': 123}
            }
        })
        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        content = json.dumps(dict(a=1,b="2"))
        encrypted_content = aes.encrypt(content)
        task = TaskFactory.create(project=project, info={
            'private_json__encrypted_payload': encrypted_content
        })

        signature = signer.dumps({'task_id': task.id})
        url = '/fileproxy/encrypted/taskpayload/%s/%s?api_key=%s&task-signature=%s' \
            % (project.id, task.id, admin.api_key, signature)

        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(url, follow_redirects=True)
            assert res.status_code == 500, res.status_code

        bad_project_id = 9999
        url = '/fileproxy/encrypted/taskpayload/%s/%s?api_key=%s&task-signature=%s' \
            % (bad_project_id, task.id, admin.api_key, signature)

        with patch.dict(self.flask_app.config, self.app_config):
            res = self.app.get(url, follow_redirects=True)
            assert res.status_code == 400, res.status_code


    @with_context
    @patch('pybossa.view.fileproxy.requests.get')
    def test_proxy_regular_user_has_lock(self, http_get):
        res = MagicMock()
        res.json.return_value = {'key': 'testkey'}
        http_get.return_value = res

        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner, info={
            'ext_config': {
                'encryption': {'key_id': 123}
            }
        })

        encryption_key = 'testkey'
        aes = AESWithGCM(encryption_key)
        content = json.dumps(dict(a=1,b="2"))
        encrypted_content = aes.encrypt(content)
        task = TaskFactory.create(project=project, info={
            'private_json__encrypted_payload': encrypted_content
        })

        signature = signer.dumps({'task_id': task.id})
        url = '/fileproxy/encrypted/taskpayload/%s/%s?api_key=%s&task-signature=%s' \
            % (project.id, task.id, user.api_key, signature)

        with patch('pybossa.view.fileproxy.has_lock') as has_lock:
            has_lock.return_value = True
            with patch.dict(self.flask_app.config, self.app_config):
                res = self.app.get(url, follow_redirects=True)
                assert res.status_code == 200, res.status_code
                assert res.data == content, res.data

        with patch('pybossa.view.fileproxy.has_lock') as has_lock:
            has_lock.return_value = False
            with patch.dict(self.flask_app.config, self.app_config):
                res = self.app.get(url, follow_redirects=True)
                assert res.status_code == 403, res.status_code

        # coowner can access the task
        project.owners_ids.append(user.id)
        with patch('pybossa.view.fileproxy.has_lock') as has_lock:
            has_lock.return_value = False
            with patch.dict(self.flask_app.config, self.app_config):
                res = self.app.get(url, follow_redirects=True)
                assert res.status_code == 200, res.status_code
