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
import json
from StringIO import StringIO
from default import with_context
from test_api import TestAPI
from mock import patch
from factories import ProjectFactory, TaskFactory
from pybossa.core import db
from pybossa.model.task_run import TaskRun
from pybossa.cloud_store_api.s3 import s3_upload_from_string
from pybossa.encryption import AESWithGCM


class TestTaskrunWithFile(TestAPI):

    host = 's3.storage.com'
    bucket = 'test_bucket'
    patch_config = {
        'S3_TASKRUN': {
            'host': host,
            'auth_headers': [('a', 'b')]
        },
        'S3_BUCKET': 'test_bucket'
    }

    def setUp(self):
        super(TestTaskrunWithFile, self).setUp()
        db.session.query(TaskRun).delete()

    @with_context
    def test_taskrun_empty_info(self):
        with patch.dict(self.flask_app.config, self.patch_config):
            project = ProjectFactory.create()
            task = TaskFactory.create(project=project)
            self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id, project.owner.api_key))

            data = dict(
                project_id=project.id,
                task_id=task.id,
                info=None
            )
            datajson = json.dumps(data)
            url = '/api/taskrun?api_key=%s' % project.owner.api_key

            success = self.app.post(url, data=datajson)
            assert success.status_code == 200, success.data

    @with_context
    @patch('pybossa.cloud_store_api.s3.boto.s3.key.Key.set_contents_from_file')
    def test_taskrun_with_upload(self, set_content):
        with patch.dict(self.flask_app.config, self.patch_config):
            project = ProjectFactory.create()
            task = TaskFactory.create(project=project)
            self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id, project.owner.api_key))

            data = dict(
                project_id=project.id,
                task_id=task.id,
                info={
                    'test__upload_url': {
                        'filename': 'hello.txt',
                        'content': 'abc'
                    }
                })
            datajson = json.dumps(data)
            url = '/api/taskrun?api_key=%s' % project.owner.api_key

            success = self.app.post(url, data=datajson)

            assert success.status_code == 200, success.data
            set_content.assert_called()
            res = json.loads(success.data)
            url = res['info']['test__upload_url']
            args = {
                'host': self.host,
                'bucket': self.bucket,
                'project_id': project.id,
                'task_id': task.id,
                'user_id': project.owner.id,
                'filename': 'hello.txt'
            }
            expected = 'https://{host}/{bucket}/{project_id}/{task_id}/{user_id}/{filename}'.format(**args)
            assert url == expected, url

    @with_context
    @patch('pybossa.cloud_store_api.s3.boto.s3.key.Key.set_contents_from_file')
    def test_taskrun_with_no_upload(self, set_content):
        with patch.dict(self.flask_app.config, self.patch_config):
            project = ProjectFactory.create()
            task = TaskFactory.create(project=project)
            self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id, project.owner.api_key))

            data = dict(
                project_id=project.id,
                task_id=task.id,
                info={
                    'test__upload_url': {
                        'test': 'not a file'
                    }
                })
            datajson = json.dumps(data)
            url = '/api/taskrun?api_key=%s' % project.owner.api_key

            success = self.app.post(url, data=datajson)

            assert success.status_code == 200, success.data
            set_content.assert_not_called()
            res = json.loads(success.data)
            assert res['info']['test__upload_url']['test'] == 'not a file'

    @with_context
    @patch('pybossa.cloud_store_api.s3.boto.s3.key.Key.set_contents_from_file')
    def test_taskrun_multipart(self, set_content):
        with patch.dict(self.flask_app.config, self.patch_config):
            project = ProjectFactory.create()
            task = TaskFactory.create(project=project)
            self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id, project.owner.api_key))
            data = dict(
                project_id=project.id,
                task_id=task.id,
                info={'field': 'value'}
            )
            datajson = json.dumps(data)

            form = {
                'request_json': datajson,
                'test__upload_url': (StringIO('Hi there'), 'hello.txt')
            }

            url = '/api/taskrun?api_key=%s' % project.owner.api_key
            success = self.app.post(url, content_type='multipart/form-data',
                                    data=form)

            assert success.status_code == 200, success.data
            set_content.assert_called()
            res = json.loads(success.data)
            url = res['info']['test__upload_url']
            args = {
                'host': self.host,
                'bucket': self.bucket,
                'project_id': project.id,
                'task_id': task.id,
                'user_id': project.owner.id,
                'filename': 'hello.txt'
            }
            expected = 'https://{host}/{bucket}/{project_id}/{task_id}/{user_id}/{filename}'.format(**args)
            assert url == expected, url

    @with_context
    @patch('pybossa.cloud_store_api.s3.boto.s3.key.Key.set_contents_from_file')
    def test_taskrun_multipart_error(self, set_content):
        with patch.dict(self.flask_app.config, self.patch_config):
            project = ProjectFactory.create()
            task = TaskFactory.create(project=project)
            self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id, project.owner.api_key))

            data = dict(
                project_id=project.id,
                task_id=task.id,
                info={'field': 'value'}
            )
            datajson = json.dumps(data)

            form = {
                'request_json': datajson,
                'test': (StringIO('Hi there'), 'hello.txt')
            }

            url = '/api/taskrun?api_key=%s' % project.owner.api_key
            success = self.app.post(url, content_type='multipart/form-data',
                                    data=form)

            assert success.status_code == 400, success.data
            set_content.assert_not_called()



class TestTaskrunWithSensitiveFile(TestAPI):

    host = 's3.storage.com'
    bucket = 'test_bucket'
    patch_config = {
        'S3_TASKRUN': {
            'host': host,
            'auth_headers': [('a', 'b')]
        },
        'ENABLE_ENCRYPTION': True,
        'S3_BUCKET': 'test_bucket',
        'FILE_ENCRYPTION_KEY': 'testkey'
    }

    def setUp(self):
        super(TestTaskrunWithSensitiveFile, self).setUp()
        db.session.query(TaskRun).delete()

    @with_context
    @patch('pybossa.cloud_store_api.s3.boto.s3.key.Key.set_contents_from_file')
    @patch('pybossa.api.task_run.s3_upload_from_string', wraps=s3_upload_from_string)
    def test_taskrun_with_upload(self, upload_from_string, set_content):
        with patch.dict(self.flask_app.config, self.patch_config):
            project = ProjectFactory.create()
            task = TaskFactory.create(project=project)
            self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id, project.owner.api_key))

            data = dict(
                project_id=project.id,
                task_id=task.id,
                info={
                    'test__upload_url': {
                        'filename': 'hello.txt',
                        'content': 'abc'
                    },
                    'another_field': 42
                })
            datajson = json.dumps(data)
            url = '/api/taskrun?api_key=%s' % project.owner.api_key

            success = self.app.post(url, data=datajson)

            assert success.status_code == 200, success.data
            set_content.assert_called()
            res = json.loads(success.data)
            assert len(res['info']) == 1
            url = res['info']['pyb_answer_url']
            args = {
                'host': self.host,
                'bucket': self.bucket,
                'project_id': project.id,
                'task_id': task.id,
                'user_id': project.owner.id,
                'filename': 'pyb_answer.json'
            }
            expected = 'https://{host}/{bucket}/{project_id}/{task_id}/{user_id}/{filename}'.format(**args)
            assert url == expected, url

            aes = AESWithGCM('testkey')
            # first call
            first_call = set_content.call_args_list[0]
            args, kwargs = first_call
            encrypted = args[0].read()
            content = aes.decrypt(encrypted)
            assert encrypted != content
            assert content == 'abc'

            upload_from_string.assert_called()
            args, kwargs = set_content.call_args
            content = aes.decrypt(args[0].read())
            actual_content = json.loads(content)

            args = {
                'host': self.host,
                'bucket': self.bucket,
                'project_id': project.id,
                'task_id': task.id,
                'user_id': project.owner.id,
                'filename': 'hello.txt'
            }
            expected = 'https://{host}/{bucket}/{project_id}/{task_id}/{user_id}/{filename}'.format(**args)
            assert actual_content['test__upload_url'] == expected
            assert actual_content['another_field'] == 42

    @with_context
    @patch('pybossa.cloud_store_api.s3.boto.s3.key.Key.set_contents_from_file')
    def test_taskrun_multipart(self, set_content):
        with patch.dict(self.flask_app.config, self.patch_config):
            project = ProjectFactory.create()
            task = TaskFactory.create(project=project)
            self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id, project.owner.api_key))

            data = dict(
                project_id=project.id,
                task_id=task.id,
                info={'field': 'value'}
            )
            datajson = json.dumps(data)

            form = {
                'request_json': datajson,
                'test__upload_url': (StringIO('Hi there'), 'hello.txt')
            }

            url = '/api/taskrun?api_key=%s' % project.owner.api_key
            success = self.app.post(url, content_type='multipart/form-data',
                                    data=form)

            assert success.status_code == 200, success.data
            set_content.assert_called()
            res = json.loads(success.data)
            url = res['info']['pyb_answer_url']
            args = {
                'host': self.host,
                'bucket': self.bucket,
                'project_id': project.id,
                'task_id': task.id,
                'user_id': project.owner.id,
                'filename': 'pyb_answer.json'
            }
            expected = 'https://{host}/{bucket}/{project_id}/{task_id}/{user_id}/{filename}'.format(**args)
            assert url == expected, url

    @with_context
    @patch('pybossa.cloud_store_api.s3.boto.s3.key.Key.set_contents_from_file')
    @patch('pybossa.api.task_run.s3_upload_from_string', wraps=s3_upload_from_string)
    @patch('pybossa.view.fileproxy.get_encryption_key')
    def test_taskrun_with_encrypted_payload(self, encr_key, upload_from_string, set_content):
        with patch.dict(self.flask_app.config, self.patch_config):
            project = ProjectFactory.create()
            encryption_key = 'testkey'
            encr_key.return_value = encryption_key
            aes = AESWithGCM(encryption_key)
            content = 'some data'
            encrypted_content = aes.encrypt(content)
            task = TaskFactory.create(project=project, info={
                'private_json__encrypted_payload': encrypted_content
            })
            self.app.get('/api/project/%s/newtask?api_key=%s' % (project.id, project.owner.api_key))

            taskrun_data = {
                'another_field': 42
            }
            data = dict(
                project_id=project.id,
                task_id=task.id,
                info=taskrun_data)
            datajson = json.dumps(data)
            url = '/api/taskrun?api_key=%s' % project.owner.api_key

            success = self.app.post(url, data=datajson)

            assert success.status_code == 200, success.data
            set_content.assert_called()
            res = json.loads(success.data)
            assert len(res['info']) == 2
            encrypted_response = res['info']['private_json__encrypted_response']
            decrypted_content = aes.decrypt(encrypted_response)
            assert decrypted_content == json.dumps(taskrun_data), "private_json__encrypted_response decrypted data mismatch"
            url = res['info']['pyb_answer_url']
            args = {
                'host': self.host,
                'bucket': self.bucket,
                'project_id': project.id,
                'task_id': task.id,
                'user_id': project.owner.id,
                'filename': 'pyb_answer.json'
            }
            expected = 'https://{host}/{bucket}/{project_id}/{task_id}/{user_id}/{filename}'.format(**args)
            assert url == expected, url
