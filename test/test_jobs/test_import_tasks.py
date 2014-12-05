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
from pybossa.jobs import import_tasks, task_repo
from pybossa.model.task import Task
from factories import AppFactory, TaskFactory
from mock import patch

class TestImportTasksJob(Test):

    @with_context
    @patch('pybossa.importers.create_tasks')
    def test_it_creates_the_new_tasks(self, create):
        app = AppFactory.create()
        template = 'csv'
        form_data = {'csv_url': 'http://google.es'}

        import_tasks(app.id, template, **form_data)

        create.assert_called_once_with(task_repo, app.id, template, **form_data)


    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('pybossa.importers.create_tasks')
    def test_sends_email_to_user_with_result_on_success(self, create, send_mail):
        create.return_value = '1 new task was imported successfully'
        app = AppFactory.create()
        template = 'csv'
        form_data = {'csv_url': 'http://google.es'}
        subject = 'Tasks Import to your project %s' % app.name
        body = 'Hello,\n\n1 new task was imported successfully to your project %s!\n\nAll the best,\nThe PyBossa team.' % app.name
        email_data = dict(recipients=[app.owner.email_addr],
                          subject=subject, body=body)

        import_tasks(app.id, template, **form_data)

        send_mail.assert_called_once_with(email_data)
