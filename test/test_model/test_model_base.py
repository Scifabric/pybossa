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
from pybossa.model.app import App
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
        app = App(
            name=u'My New Project',
            short_name=u'my-new-app',
            description=u'description',
            info=info)
        category = Category(name=u'cat', short_name=u'cat', description=u'cat')
        app.category = category
        app.owner = user
        task_info = {
            'question': 'My random question',
            'url': 'my url'}
        task = Task(info=task_info)
        task_run_info = {'answer': u'annakarenina'}
        task_run = TaskRun(info=task_run_info)
        task.app = app
        task_run.task = task
        task_run.app = app
        task_run.user = user
        db.session.add_all([user, app, task, task_run])
        db.session.commit()
        app_id = app.id

        db.session.remove()

        app = db.session.query(App).get(app_id)
        assert app.name == u'My New Project', app
        # year would start with 201...
        assert app.created.startswith('201'), app.created
        assert app.long_tasks == 0, app.long_tasks
        assert app.hidden == 0, app.hidden
        assert app.time_estimate == 0, app
        assert app.time_limit == 0, app
        assert app.calibration_frac == 0, app
        assert app.bolt_course_id == 0
        assert len(app.tasks) == 1, app
        assert app.owner.name == username, app
        out_task = app.tasks[0]
        assert out_task.info['question'] == task_info['question'], out_task
        assert out_task.quorum == 0, out_task
        assert out_task.state == "ongoing", out_task
        assert out_task.calibration == 0, out_task
        assert out_task.priority_0 == 0, out_task
        assert len(out_task.task_runs) == 1, out_task
        outrun = out_task.task_runs[0]
        assert outrun.info['answer'] == task_run_info['answer'], outrun
        assert outrun.user.name == username, outrun


