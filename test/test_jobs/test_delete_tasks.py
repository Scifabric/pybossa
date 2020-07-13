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
from default import Test, with_context, flask_app, db
from factories import ProjectFactory, UserFactory, TaskFactory, TaskRunFactory
from pybossa.jobs import delete_bulk_tasks
from pybossa.repositories import TaskRepository
from mock import patch, MagicMock

task_repo = TaskRepository(db)

class TestDeleteTasks(Test):

    @with_context
    @patch('pybossa.core.db')
    @patch('pybossa.jobs.send_mail')
    def test_delete_bulk_tasks(self, mock_send_mail, mock_db):
        """Test delete_bulk_tasks deletes tasks and sends email"""
        user = UserFactory.create(admin=True)
        project = ProjectFactory.create(name='test_project')
        TaskFactory.create_batch(5, project=project)
        tasks = task_repo.filter_tasks_by(project_id=project.id)
        assert len(tasks) == 5

        data = {'project_id': project.id, 'project_name': project.name,
        'curr_user': user.email_addr, 'force_reset': 'true',
        'coowners': [], 'current_user_fullname': user.fullname,
        'url': flask_app.config.get('SERVER_URL')}

        delete_bulk_tasks(data)

        mock_db.bulkdel_session.execute.assert_called_once()

        expected_subject = "Tasks deletion from {0}".format(project.name)
        msg_str = "Hello,\n\nTasks, taskruns and results associated have been deleted from project {0} on {1} as requested by {2}\n\nThe {3} team."
        expected_body = msg_str.format(project.name,
                                       flask_app.config.get("SERVER_URL"), 
                                       user.fullname,
                                       flask_app.config.get("BRAND")
                                       )
        expected = dict(recipients=[user.email_addr], subject=expected_subject, body=expected_body)
        mock_send_mail.assert_called_once_with(expected)
