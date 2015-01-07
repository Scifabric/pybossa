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

from pybossa.model import webhook
from default import Test, with_context
from factories import AppFactory
from factories import TaskFactory
from factories import TaskRunFactory
from redis import StrictRedis
from rq_scheduler import Scheduler
from mock import patch, MagicMock
from datetime import datetime

queue = MagicMock()
queue.enqueue.return_value = True


class TestWebHooks(Test):

    def setUp(self):
        super(TestWebHooks, self).setUp()
        self.connection = StrictRedis()
        self.connection.flushall()
        self.scheduler = Scheduler('test_queue', connection=self.connection)


    @with_context
    @patch('pybossa.model.requests')
    def test_webhooks(self, mock):
        """Test WEBHOOK works."""
        mock.post.return_value = True
        err_msg = "The webhook should return True from patched method"
        assert webhook('url'), err_msg
        err_msg = "The post method should be called"
        assert mock.post.called, err_msg

    @with_context
    @patch('pybossa.model.requests')
    def test_webhooks_without_url(self, mock):
        """Test WEBHOOK without url works."""
        mock.post.return_value = True
        err_msg = "The webhook should return False"
        assert webhook(None) is False, err_msg

    @with_context
    @patch('pybossa.model.task_run.webhook_queue', new=queue)
    def test_trigger_webhook_without_url(self):
        """Test WEBHOOK is triggered without url."""
        app = AppFactory.create()
        task = TaskFactory.create(app=app, n_answers=1)
        TaskRunFactory.create(app=app, task=task)
        assert queue.enqueue.called is False, queue.enqueue.called
        queue.reset_mock()

    @with_context
    @patch('pybossa.model.task_run.webhook_queue', new=queue)
    def test_trigger_webhook_with_url_not_completed_task(self):
        """Test WEBHOOK is not triggered for uncompleted tasks."""
        import random
        app = AppFactory.create()
        task = TaskFactory.create(app=app)
        for i in range(1, random.randrange(2, 5)):
            TaskRunFactory.create(app=app, task=task)
        assert queue.enqueue.called is False, queue.enqueue.called
        assert task.state != 'completed'
        queue.reset_mock()


    @with_context
    @patch('pybossa.model.task_run.webhook_queue', new=queue)
    def test_trigger_webhook_with_url(self):
        """Test WEBHOOK is triggered with url."""
        url = 'http://server.com'
        app = AppFactory.create(webhook=url,)
        task = TaskFactory.create(app=app, n_answers=1)
        TaskRunFactory.create(app=app, task=task)
        payload = dict(event='task_completed',
                       app_short_name=app.short_name,
                       app_id=app.id,
                       task_id=task.id,
                       fired_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        assert queue.enqueue.called
        assert queue.called_with(webhook, url, payload)
        queue.reset_mock()
