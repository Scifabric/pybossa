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


class TestTaskrunWithFile(TestAPI):

    host = 's3.storage.com'
    bucket = 'test_bucket'
    patch_config = {
        'S3_CONN_KWARGS': {'host': host},
        'S3_CUSTOM_HANDLER_HOSTS': [host],
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
    @patch('pybossa.uploader.s3_uploader.boto.s3.key.Key.set_contents_from_filename')
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
    @patch('pybossa.uploader.s3_uploader.boto.s3.key.Key.set_contents_from_filename')
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
    @patch('pybossa.uploader.s3_uploader.boto.s3.key.Key.set_contents_from_filename')
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
    @patch('pybossa.uploader.s3_uploader.boto.s3.key.Key.set_contents_from_filename')
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
