# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

from default import Test, db, with_context
from nose.tools import raises
from pybossa.model.user import User
from pybossa.model.project import Project
from pybossa.model.task import Task
from pybossa.model.category import Category
from pybossa.model.task_run import TaskRun


"""Tests for inter-model relations and base classes and helper functions
of model package."""



class TestModelBase(Test):

    @raises(NotImplementedError)
    @with_context
    def test_domain_object_error(self):
        """Test DomainObject errors work."""
        user = User()
        user.name = "John"
        d = user.dictize()
        user.undictize(d)


    @with_context
    def test_all(self):
        """Test MODEL works"""
        username = u'test-user-1'
        user = User(name=username, fullname=username, email_addr=username)
        info = {
            'total': 150,
            'long_description': 'hello world'}
        project = Project(
            name=u'My New Project',
            short_name=u'my-new-app',
            description=u'description',
            info=info)
        category = Category(name=u'cat', short_name=u'cat', description=u'cat')
        project.category = category
        project.owner = user
        task_info = {
            'question': 'My random question',
            'url': 'my url'}
        task = Task(info=task_info)
        task_run_info = {'answer': u'annakarenina'}
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
        assert project.name == u'My New Project', project
        # year would start with 201...
        assert project.created.startswith('201'), project.created
        assert project.long_tasks == 0, project.long_tasks
        assert project.hidden == 0, project.hidden
        assert project.time_estimate == 0, project
        assert project.time_limit == 0, project
        assert project.calibration_frac == 0, project
        assert project.bolt_course_id == 0
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


