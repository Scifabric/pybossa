# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
from pybossa.jobs import import_tasks
from pybossa.model.task import Task
from factories import AppFactory, TaskFactory
from mock import patch

class TestImportTasksJob(Test):

    @with_context
    def test_it_creates_the_new_tasks(self):
        app = AppFactory.create()
        tasks_info = [{'info': {'Bar': '2', 'Foo': '1', 'Baz': '3'}}]

        import_tasks(tasks_info, app.id)

        task = db.session.query(Task).first()
        assert task is not None, "No task was created"
        assert {'Bar': '2', 'Foo': '1', 'Baz': '3'} == task.info, task.info


    @with_context
    def test_it_does_not_create_task_if_already_exists(self):
        tasks_info = [{'info': {'Bar': '2', 'Foo': '1', 'Baz': '3'}}]
        app = AppFactory.create()
        task = TaskFactory.create(app=app, info=tasks_info[0]['info'])

        import_tasks(tasks_info, app.id)

        tasks = db.session.query(Task).all()
        assert len(tasks) == 1, tasks


    @with_context
    @patch('pybossa.jobs.send_mail')
    def test_sends_email_to_user_with_result(self, send_mail):
        app = AppFactory.create()
        tasks_info = [{'info': {'Bar': '2', 'Foo': '1', 'Baz': '3'}}]
        subject = 'Tasks Import to your project %s' % app.name
        body = 'Hello,\n\nThe tasks you recently imported to your project at PyBossa have been successfully created.\n\nAll the best,\nThe team.'
        email_data = dict(recipients=[app.owner.email_addr],
                          subject=subject, body=body)

        import_tasks(tasks_info, app.id)

        send_mail.assert_called_once_with(email_data)
