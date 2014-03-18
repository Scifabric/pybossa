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

from base import model, db, redis_flushall
from nose.tools import raises, assert_raises
from sqlalchemy.exc import IntegrityError


class TestModel:
    @classmethod
    def setUp(self):
        model.rebuild_db()

    def tearDown(self):
        db.session.remove()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()
        redis_flushall()

    @raises(NotImplementedError)
    def test_domain_object_error(self):
        """Test DomainObject errors work."""
        user = model.User()
        user.name = "John"
        d = user.dictize()
        user.undictize(d)

    def test_user(self):
        """Test USER model."""
        # First user
        user = model.User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            locale="en")

        user2 = model.User(
            email_addr="john.doe2@example.com",
            name="johndoe2",
            fullname="John Doe2",
            locale="en",)

        db.session.add(user)
        db.session.commit()
        tmp = db.session.query(model.User).get(1)
        assert tmp.email_addr == user.email_addr, tmp
        assert tmp.name == user.name, tmp
        assert tmp.fullname == user.fullname, tmp
        assert tmp.locale == user.locale, tmp
        assert tmp.api_key is not None, tmp
        assert tmp.created is not None, tmp
        err_msg = "First user should be admin"
        assert tmp.admin is True, err_msg
        err_msg = "check_password method should return False"
        assert tmp.check_password(password="nothing") is False, err_msg

        db.session.add(user2)
        db.session.commit()
        tmp = db.session.query(model.User).get(2)
        assert tmp.email_addr == user2.email_addr, tmp
        assert tmp.name == user2.name, tmp
        assert tmp.fullname == user2.fullname, tmp
        assert tmp.locale == user2.locale, tmp
        assert tmp.api_key is not None, tmp
        assert tmp.created is not None, tmp
        err_msg = "Second user should be not an admin"
        assert tmp.admin is False, err_msg

    def test_user_errors(self):
        """Test USER model errors."""
        user = model.User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            locale="en")

        # User.name should not be nullable
        user.name = None
        db.session.add(user)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # User.fullname should not be nullable
        user.name = "johndoe"
        user.fullname = None
        db.session.add(user)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # User.email_addr should not be nullable
        user.name = "johndoe"
        user.fullname = "John Doe"
        user.email_addr = None
        db.session.add(user)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

    def test_app_repr(self):
        """Test APP model repr works."""
        app = model.App(
            id=1,
            name='Application',
            short_name='app',
            description='desc',
            owner_id=None)

        assert app.__repr__() == 'App(1)'

    def test_app_errors(self):
        """Test APP model errors."""
        app = model.App(
            name='Application',
            short_name='app',
            description='desc',
            owner_id=None)

        # App.owner_id shoult not be nullable
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # App.name shoult not be nullable
        user = model.User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            locale="en")
        db.session.add(user)
        db.session.commit()
        user = db.session.query(model.User).first()
        app.owner_id = user.id
        app.name = None
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        app.name = ''
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # App.short_name shoult not be nullable
        app.name = "Application"
        app.short_name = None
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        app.short_name = ''
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # App.description shoult not be nullable
        db.session.add(app)
        app.short_name = "app"
        app.description = None
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        app.description = ''
        db.session.add(app)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()


    def test_task_errors(self):
        """Test TASK model errors."""
        user = model.User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            locale="en")
        db.session.add(user)
        db.session.commit()
        user = db.session.query(model.User).first()
        app = model.App(
            name='Application',
            short_name='app',
            description='desc',
            owner_id=user.id)
        db.session.add(app)
        db.session.commit()

        task = model.Task(app_id=None)
        db.session.add(task)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

    def test_task_run_errors(self):
        """Test TASK_RUN model errors."""
        user = model.User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            locale="en")
        db.session.add(user)
        db.session.commit()

        user = db.session.query(model.User).first()
        app = model.App(
            name='Application',
            short_name='app',
            description='desc',
            owner_id=user.id)
        db.session.add(app)
        db.session.commit()

        task = model.Task(app_id=app.id)
        db.session.add(task)
        db.session.commit()

        task_run = model.TaskRun(app_id=None, task_id=task.id)
        db.session.add(task_run)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        task_run = model.TaskRun(app_id=app.id, task_id=None)
        db.session.add(task_run)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

    def test_all(self):
        """Test MODEL works"""
        username = u'test-user-1'
        user = model.User(name=username, fullname=username, email_addr=username)
        info = {
            'total': 150,
            'long_description': 'hello world'}
        app = model.App(
            name=u'My New App',
            short_name=u'my-new-app',
            description=u'description',
            info=info)
        app.owner = user
        task_info = {
            'question': 'My random question',
            'url': 'my url'}
        task = model.Task(info=task_info)
        task_run_info = {'answer': u'annakarenina'}
        task_run = model.TaskRun(info=task_run_info)
        task.app = app
        task_run.task = task
        task_run.app = app
        task_run.user = user
        db.session.add_all([user, app, task, task_run])
        db.session.commit()
        app_id = app.id

        db.session.remove()

        app = db.session.query(model.App).get(app_id)
        assert app.name == u'My New App', app
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

        user = model.User.by_name(username)
        assert user.apps[0].id == app_id, user

#    def test_user(self):
#        """Test MODEL User works"""
#        user = model.User(name=u'test-user', email_addr=u'test@xyz.org')
#        db.session.add(user)
#        db.session.commit()
#
#        db.session.remove()
#        user = model.User.by_name(u'test-user')
#        assert user, user
#        assert len(user.api_key) == 36, user
#
#        out = user.dictize()
#        assert out['name'] == u'test-user', out
