# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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

import json
from pybossa.jobs import webhook
from default import Test, with_context, FakeResponse
from factories import ProjectFactory
from factories import TaskFactory
from factories import TaskRunFactory
from redis import StrictRedis
from mock import patch, MagicMock
from datetime import datetime

queue = MagicMock()
queue.enqueue.return_value = True


class TestWebHooks(Test):

    def setUp(self):
        super(TestWebHooks, self).setUp()
        self.connection = StrictRedis()
        self.connection.flushall()
        self.project = ProjectFactory.create()
        self.webhook_payload = dict(project_id=self.project.id,
                                    project_short_name=self.project.short_name)


    @with_context
    @patch('pybossa.jobs.requests.post')
    def test_webhooks(self, mock):
        """Test WEBHOOK works."""
        mock.return_value = FakeResponse(text=json.dumps(dict(foo='bar')),
                                                              status_code=200)
        err_msg = "The webhook should return True from patched method"
        assert webhook('url', self.webhook_payload), err_msg
        err_msg = "The post method should be called"
        assert mock.called, err_msg

    @with_context
    @patch('pybossa.jobs.requests.post')
    def test_webhooks_without_url(self, mock):
        """Test WEBHOOK without url works."""
        mock.post.return_value = True
        err_msg = "The webhook should return Connection Error"
        res = webhook(None, self.webhook_payload, None)
        assert res.response == 'Connection Error', err_msg
        assert res.response_status_code is None, err_msg

    @with_context
    @patch('pybossa.model.event_listeners.webhook_queue', new=queue)
    def test_trigger_webhook_without_url(self):
        """Test WEBHOOK is triggered without url."""
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project, n_answers=1)
        TaskRunFactory.create(project=project, task=task)
        assert queue.enqueue.called is False, queue.enqueue.called
        queue.reset_mock()

    @with_context
    @patch('pybossa.model.event_listeners.webhook_queue', new=queue)
    def test_trigger_webhook_with_url_not_completed_task(self):
        """Test WEBHOOK is not triggered for uncompleted tasks."""
        import random
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        for i in range(1, random.randrange(2, 5)):
            TaskRunFactory.create(project=project, task=task)
        assert queue.enqueue.called is False, queue.enqueue.called
        assert task.state != 'completed'
        queue.reset_mock()


    @with_context
    @patch('pybossa.model.event_listeners.webhook_queue', new=queue)
    def test_trigger_webhook_with_url(self):
        """Test WEBHOOK is triggered with url."""
        url = 'http://server.com'
        project = ProjectFactory.create(webhook=url,)
        task = TaskFactory.create(project=project, n_answers=1)
        TaskRunFactory.create(project=project, task=task)
        payload = dict(event='task_completed',
                       project_short_name=project.short_name,
                       project_id=project.id,
                       task_id=task.id,
                       fired_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        assert queue.enqueue.called
        assert queue.called_with(webhook, url, payload)
        queue.reset_mock()
