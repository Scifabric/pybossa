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

from default import Test, db, with_context, flask_app
from factories import BlogpostFactory
from factories import TaskRunFactory
from factories import ProjectFactory
from factories import UserFactory
from mock import patch, MagicMock
from pybossa.jobs import check_and_send_task_notifications, notify_task_progress

queue = MagicMock()
queue.enqueue.return_value = True

class TestSendTaskNotification(Test):

    @with_context
    @patch('pybossa.jobs.n_available_tasks')
    @patch('pybossa.jobs.notify_task_progress')
    def test_remaining_tasks_drop_below_configuration_0(self, notify, n_tasks):
        """Send email if remaining tasks drops below, test with connection"""
        n_tasks.return_value = 0
        reminder = dict(target_remaining=0, sent=False)
        conn = MagicMock()
        conn.execute.return_value = None
        project_id = '1'
        project = ProjectFactory.create(id=project_id,
                                        owners_ids=[],
                                        published=True,
                                        featured=True,
                                        info={'progress_reminder':reminder})

        check_and_send_task_notifications(project_id, conn)
        assert notify.called
        assert project.info['progress_reminder']['sent']


    @with_context
    @patch('pybossa.jobs.n_available_tasks')
    @patch('pybossa.jobs.notify_task_progress')
    def test_remaining_tasks_drop_below_configuration_1(self, notify, n_tasks):
        """Send email if remaining tasks drops below"""
        n_tasks.return_value = 0
        reminder = dict(target_remaining=0, sent=False)
        project_id = '1'
        project = ProjectFactory.create(id=project_id,
                                        owners_ids=[],
                                        published=True,
                                        featured=True,
                                        info={'progress_reminder':reminder})

        check_and_send_task_notifications(project_id)
        assert notify.called
        assert project.info['progress_reminder']['sent']


    @with_context
    @patch('pybossa.jobs.n_available_tasks')
    @patch('pybossa.jobs.notify_task_progress')
    def test_remaining_tasks_drop_below_configuration_2(self, notify, n_tasks):
        """Do not sent multiple email"""
        n_tasks.return_value = 0
        reminder = dict(target_remaining=0, sent=True)
        project_id = '1'
        project = ProjectFactory.create(id=project_id,
                                        owners_ids=[],
                                        published=True,
                                        featured=True,
                                        info={'progress_reminder':reminder})

        check_and_send_task_notifications(project_id)
        assert not notify.called
        assert project.info['progress_reminder']['sent']


    @with_context
    @patch('pybossa.jobs.n_available_tasks')
    @patch('pybossa.jobs.notify_task_progress')
    def test_remaining_tasks_do_not_drop_below_configuration(self, notify, n_tasks):
        """Do not send email if #remaining tasks is greater than configuration"""
        n_tasks.return_value = 1
        reminder = dict(target_remaining=0, sent=False)
        project_id = '1'
        project = ProjectFactory.create(id=project_id,
                                        owners_ids=[],
                                        published=True,
                                        featured=True,
                                        info={'progress_reminder':reminder})

        check_and_send_task_notifications(project_id)
        assert not notify.called
        assert not project.info['progress_reminder']['sent']


    @with_context
    @patch('pybossa.jobs.n_available_tasks')
    @patch('pybossa.jobs.notify_task_progress')
    def test_remaining_tasks_do_not_drop_below_configuration_2(self, notify, n_tasks):
        """Do not send email if #remaining tasks is greater than configuration"""
        n_tasks.return_value = 1
        reminder = dict(target_remaining=0, sent=True)
        project_id = '1'
        project = ProjectFactory.create(id=project_id,
                                        owners_ids=[],
                                        published=True,
                                        featured=True,
                                        info={'progress_reminder':reminder})

        check_and_send_task_notifications(project_id)
        assert not notify.called
        assert not project.info['progress_reminder']['sent']

    @with_context
    @patch('pybossa.jobs.requests')
    @patch('pybossa.jobs.n_available_tasks')
    @patch('pybossa.jobs.notify_task_progress')
    def test_remaining_tasks_drop_below_configuration_hitting_webhook(self, notify, n_tasks, req):
        """Send email if remaining tasks drops below, test with connection"""
        n_tasks.return_value = 0
        reminder = dict(target_remaining=0, webhook="fake_url", sent=False)
        conn = MagicMock()
        conn.execute.return_value = None
        project_id = '1'
        project = ProjectFactory.create(id=project_id,
                                        owners_ids=[],
                                        published=True,
                                        featured=True,
                                        info={'progress_reminder':reminder})

        check_and_send_task_notifications(project_id, conn)
        assert req.post.called
        assert project.info['progress_reminder']['sent']

    @with_context
    @patch('pybossa.jobs.requests')
    @patch('pybossa.jobs.n_available_tasks')
    @patch('pybossa.jobs.notify_task_progress')
    def test_remaining_tasks_drop_below_configuration_hitting_webhook_failed(self, notify, n_tasks, req):
        """Send email if remaining tasks drops below, test with connection"""
        n_tasks.return_value = 0
        req.post.side_effect = Exception('not found')
        reminder = dict(target_remaining=0, webhook="fake_url", sent=False)
        conn = MagicMock()
        conn.execute.return_value = None
        project_id = '1'
        project = ProjectFactory.create(id=project_id,
                                        owners_ids=[],
                                        published=True,
                                        featured=True,
                                        info={'progress_reminder':reminder})

        check_and_send_task_notifications(project_id, conn)
        assert req.post.called
        assert project.info['progress_reminder']['sent']

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('pybossa.jobs.requests')
    @patch('pybossa.jobs.n_available_tasks')
    @patch('pybossa.jobs.notify_task_progress')
    def test_remaining_tasks_drop_below_configuration_hitting_webhook_return_400(self, notify, n_tasks, req, mail):
        """Send email if remaining tasks drops below, test with connection"""
        n_tasks.return_value = 0
        req.post.return_value.status_code = 400
        reminder = dict(target_remaining=0, webhook="fake_url", sent=False)
        conn = MagicMock()
        conn.execute.return_value = None
        project_id = '1'
        project = ProjectFactory.create(id=project_id,
                                        owners_ids=[],
                                        published=True,
                                        featured=True,
                                        info={'progress_reminder':reminder})

        check_and_send_task_notifications(project_id, conn)
        assert req.post.called
        assert mail.called
        assert project.info['progress_reminder']['sent']

    @with_context
    @patch('pybossa.jobs.enqueue_job')
    def test_notify_task_progress(self, mock):
        info = dict(project_name="test project", n_available_tasks=10)
        email_addr = ['user@user.com']
        notify_task_progress(info, email_addr)
        assert mock.called