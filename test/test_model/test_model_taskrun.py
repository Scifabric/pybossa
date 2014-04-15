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
from nose.tools import assert_raises
from sqlalchemy.exc import IntegrityError
from pybossa.model.user import User
from pybossa.model.app import App
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun


class TestModelTaskRun(Test):

    @with_context
    def test_task_run_errors(self):
        """Test TASK_RUN model errors."""
        user = User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            locale="en")
        db.session.add(user)
        db.session.commit()

        user = db.session.query(User).first()
        app = App(
            name='Application',
            short_name='app',
            description='desc',
            owner_id=user.id)
        db.session.add(app)
        db.session.commit()

        task = Task(app_id=app.id)
        db.session.add(task)
        db.session.commit()

        task_run = TaskRun(app_id=None, task_id=task.id)
        db.session.add(task_run)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        task_run = TaskRun(app_id=app.id, task_id=None)
        db.session.add(task_run)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()
