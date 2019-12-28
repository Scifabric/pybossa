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
from nose.tools import assert_raises
from sqlalchemy.exc import IntegrityError
from pybossa.model.user import User
from pybossa.model.project import Project
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.category import Category


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
        category = Category(name='cat', short_name='cat', description='cat')
        project = Project(name='Application', short_name='app', description='desc',
                  owner_id=user.id, category=category)
        db.session.add(project)
        db.session.commit()

        task = Task(project_id=project.id)
        db.session.add(task)
        db.session.commit()

        task_run = TaskRun(project_id=None, task_id=task.id)
        db.session.add(task_run)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        task_run = TaskRun(project_id=project.id, task_id=None)
        db.session.add(task_run)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()
