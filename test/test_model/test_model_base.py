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

from default import Test, db, with_context
from nose.tools import raises
from pybossa.model.user import User
from pybossa.model.project import Project
from pybossa.model.task import Task
from pybossa.model.category import Category
from pybossa.model.task_run import TaskRun
from mock import patch


"""Tests for inter-model relations and base classes and helper functions
of model package."""


class TestModelBase(Test):

    """Test class for DomainObject methods."""

    @raises(NotImplementedError)
    @with_context
    def test_domain_object_error(self):
        """Test DomainObject errors work."""
        user = User()
        user.name = "John"
        d = user.dictize()
        user.undictize(d)

    @with_context
    def test_to_public_json(self):
        """Test DomainObject to_public_json method works."""
        user = User()
        user.name = 'daniel'
        user_dict = user.dictize()
        json = user.to_public_json()
        err_msg = "Wrong value"
        assert json['name'] == user.name, err_msg
        err_msg = "Missing fields"
        assert list(json.keys()).sort() == user.public_attributes().sort(), err_msg

        json = user.to_public_json(data=user_dict)
        err_msg = "Wrong value"
        assert json['name'] == user.name, err_msg
        err_msg = "Missing fields"
        assert list(json.keys()).sort() == user.public_attributes().sort(), err_msg

    @with_context
    def test_info_public_keys(self):
        """Test DomainObject to_public_json method works."""
        user = User()
        user.name = 'daniel'
        user.info = dict(container='3', avatar='img.png',
                         token='secret',
                         badges=['awesome.png',
                                 'incredible.png'],
                         hidden=True)
        user_dict = user.dictize()
        json = user.to_public_json()
        err_msg = "Wrong value"
        assert json['name'] == user.name, err_msg
        err_msg = "Missing fields"
        assert list(json.keys()).sort() == user.public_attributes().sort(), err_msg
        err_msg = "There should be info keys"
        assert json['info']['container'] == '3', err_msg
        assert json['info']['avatar'] == 'img.png', err_msg
        err_msg = "This key should be missing"
        assert json['info'].get('token') is None, err_msg

        json = user.to_public_json(data=user_dict)
        err_msg = "Wrong value"
        assert json['name'] == user.name, err_msg
        err_msg = "Missing fields"
        assert list(json.keys()).sort() == user.public_attributes().sort(), err_msg
        err_msg = "There should be info keys"
        assert json['info']['container'] == '3', err_msg
        assert json['info']['avatar'] == 'img.png', err_msg
        err_msg = "This key should be missing"
        assert json['info'].get('token') is None, err_msg

        with patch.dict(self.flask_app.config, {'USER_INFO_PUBLIC_FIELDS': ['badges']}):
            json = user.to_public_json()
            assert list(json['info'].keys()).sort() == User().public_info_keys().sort(), err_msg
            assert 'badges' in list(json['info'].keys())
            assert 'hidden' not in list(json['info'].keys())


    @with_context
    def test_info_public_keys_extension(self):
        """Test DomainObject to_public_json method works with extra fields."""
        project = Project()
        project.name = 'test'
        project.short_name = 'test'
        project.description = 'Desc'
        project.info = dict(container='3',
                            thumbnail='img.png',
                            token='secret',
                            tutorial='help',
                            sched='default',
                            task_presenter='something',
                            super_secret='hidden',
                            public_field='so true')
        project_dict = project.dictize()
        json = project.to_public_json()
        err_msg = "Wrong value"
        assert json['name'] == project.name, err_msg
        err_msg = "Missing fields"
        assert list(json.keys()).sort() == project.public_attributes().sort(), err_msg
        err_msg = "There should be info keys"
        assert list(json['info'].keys()).sort() == Project().public_info_keys().sort(), err_msg
        with patch.dict(self.flask_app.config, {'PROJECT_INFO_PUBLIC_FIELDS': ['public_field']}):
            json = project.to_public_json()
            assert list(json['info'].keys()).sort() == Project().public_info_keys().sort(), err_msg
            assert 'public_field' in list(json['info'].keys())
            assert 'secret_key' not in list(json['info'].keys())

    @with_context
    def test_all(self):
        """Test MODEL works"""
        username = 'test-user-1'
        user = User(name=username, fullname=username, email_addr=username)
        info = {
            'total': 150,
            'long_description': 'hello world'}
        project = Project(
            name='My New Project',
            short_name='my-new-app',
            description='description',
            info=info)
        category = Category(name='cat', short_name='cat', description='cat')
        project.category = category
        project.owner = user
        task_info = {
            'question': 'My random question',
            'url': 'my url'}
        task = Task(info=task_info)
        task_run_info = {'answer': 'annakarenina'}
        task_run = TaskRun(info=task_run_info)
        task.project = project
        task_run.task = task
        task_run.project = project
        task_run.user = user
        db.session.add_all([user, project, task, task_run])
        db.session.commit()
        project_id = project.id

        db.session.remove()

        project = db.session.query(Project).get(project_id)
        assert project.name == 'My New Project', project
        # year would start with 202...
        assert project.created.startswith('202'), project.created
        assert len(project.tasks) == 1, project
        assert project.owner.name == username, project
        out_task = project.tasks[0]
        assert out_task.info['question'] == task_info['question'], out_task
        assert out_task.quorum == 0, out_task
        assert out_task.state == "ongoing", out_task
        assert out_task.calibration == 0, out_task
        assert out_task.priority_0 == 0, out_task
        assert len(out_task.task_runs) == 1, out_task
        outrun = out_task.task_runs[0]
        assert outrun.info['answer'] == task_run_info['answer'], outrun
        assert outrun.user.name == username, outrun
