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

import json
import requests
from pybossa.jobs import webhook
from default import Test, with_context, FakeResponse, db
from factories import ProjectFactory
from factories import TaskFactory
from factories import TaskRunFactory
from factories import WebhookFactory
from factories import UserFactory
from mock import patch, MagicMock
from datetime import datetime
from pybossa.repositories import ResultRepository, WebhookRepository
from pybossa.core import sentinel

queue = MagicMock()
queue.enqueue.return_value = True

result_repo = ResultRepository(db)
webhook_repo = WebhookRepository(db)


class TestWebHooks(Test):

    @with_context
    def setUp(self):
        super(TestWebHooks, self).setUp()
        self.connection = sentinel.master
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
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        mock.assert_called_with('url', params=dict(),
                                data=json.dumps(self.webhook_payload),
                                headers=headers)


    @with_context
    @patch('pybossa.jobs.requests.post')
    def test_webhooks_rerun(self, mock):
        """Test WEBHOOK rerun works."""
        mock.return_value = FakeResponse(text=json.dumps(dict(foo='bar')),
                                         status_code=200)
        assert webhook('url', self.webhook_payload, rerun=True), err_msg
        err_msg = "The post method should be called"
        assert mock.called, err_msg
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        mock.assert_called_with('url', params=dict(rerun=True),
                                data=json.dumps(self.webhook_payload),
                                headers=headers)

    @with_context
    @patch('pybossa.jobs.requests.post')
    def test_webhooks_connection_error(self, mock):
        """Test WEBHOOK with connection error works."""
        import requests
        from pybossa.core import webhook_repo
        mock.side_effect = requests.exceptions.ConnectionError
        err_msg = "A webhook should be returned"
        res = webhook('url', self.webhook_payload)
        assert res.response == 'Connection Error', err_msg
        assert res.response_status_code == None, err_msg
        wh = webhook_repo.get(1)
        assert wh.response == res.response, err_msg
        assert wh.response_status_code == res.response_status_code, err_msg

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
        owner = UserFactory.create(pro=True)
        project = ProjectFactory.create(webhook=url,owner=owner)
        task = TaskFactory.create(project=project, n_answers=1)
        TaskRunFactory.create(project=project, task=task)
        result = result_repo.get_by(project_id=project.id, task_id=task.id)
        payload = dict(event='task_completed',
                       project_short_name=project.short_name,
                       project_id=project.id,
                       task_id=task.id,
                       result_id=result.id,
                       fired_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        assert queue.enqueue.called
        assert queue.called_with(webhook, url, payload)

        u = '/project/%s/webhook?api_key=%s&all=1' % (project.short_name,
                                                      project.owner.api_key)
        res = self.app.get(u)
        assert queue.enqueue.called
        assert queue.called_with(webhook, url, payload, True)

        wh = WebhookFactory(response_status_code=500, project_id=project.id,
                            payload=payload, response="500")
        u = '/project/%s/webhook?api_key=%s&failed=1' % (project.short_name,
                                                         project.owner.api_key)
        res = self.app.get(u)
        assert queue.enqueue.called
        assert queue.called_with(webhook, url, payload, True)

        u = '/project/%s/webhook/%s?api_key=%s&failed=1' % (wh.id,
                                                            project.short_name,
                                                            project.owner.api_key)
        res = self.app.post(u)
        assert queue.enqueue.called
        assert queue.called_with(webhook, url, payload, True)

        queue.reset_mock()

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('pybossa.jobs.requests.post')
    def test_trigger_fails_webhook_with_url(self, mock_post, mock_send_mail):
        """Test WEBHOOK fails and sends email is triggered."""
        response = MagicMock()
        response.text = "<html>Something broken</html>"
        response.status_code = 500
        mock_post.return_value = response
        project = ProjectFactory.create(published=True)
        payload = dict(event='task_completed',
                       project_short_name=project.short_name,
                       project_id=project.id,
                       task_id=1,
                       result_id=1,
                       fired_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        wbh = WebhookFactory.create()
        tmp = webhook('url', payload=payload, oid=wbh.id)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        mock_post.assert_called_with('url', data=json.dumps(payload),
                                     headers=headers,
                                     params={})
        subject = "Broken: %s webhook failed" % project.name
        body = 'Sorry, but the webhook failed'
        mail_dict = dict(recipients=self.flask_app.config.get('ADMINS'),
                         subject=subject, body=body, html=tmp.response)
        mock_send_mail.assert_called_with(mail_dict)

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('pybossa.jobs.requests.post')
    def test_trigger_fails_webhook_with_no_url(self, mock_post, mock_send_mail):
        """Test WEBHOOK fails and sends email is triggered when no URL or failed connection."""
        mock_post.side_effect = requests.exceptions.ConnectionError('Not URL')
        project = ProjectFactory.create(published=True)
        payload = dict(event='task_completed',
                       project_short_name=project.short_name,
                       project_id=project.id,
                       task_id=1,
                       result_id=1,
                       fired_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        wbh = WebhookFactory.create()
        tmp = webhook(None, payload=payload, oid=wbh.id)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        #mock_post.assert_called_with('url', data=json.dumps(payload), headers=headers)
        subject = "Broken: %s webhook failed" % project.name
        body = 'Sorry, but the webhook failed'
        mail_dict = dict(recipients=self.flask_app.config.get('ADMINS'),
                         subject=subject, body=body, html=tmp.response)
        mock_send_mail.assert_called_with(mail_dict)

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('pybossa.jobs.requests.post', side_effect=requests.exceptions.ConnectionError())
    def test_trigger_fails_webhook_with_url_connection_error(self, mock_post, mock_send_mail):
        """Test WEBHOOK fails and sends email is triggered when there is a connection error."""
        project = ProjectFactory.create(published=True)
        payload = dict(event='task_completed',
                       project_short_name=project.short_name,
                       project_id=project.id,
                       task_id=1,
                       result_id=1,
                       fired_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        wbh = WebhookFactory.create()
        tmp = webhook('url', payload=payload, oid=wbh.id)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        mock_post.assert_called_with('url', data=json.dumps(payload),
                                     headers=headers,
                                     params={})
        subject = "Broken: %s webhook failed" % project.name
        body = 'Sorry, but the webhook failed'
        mail_dict = dict(recipients=self.flask_app.config.get('ADMINS'),
                         subject=subject, body=body, html=tmp.response)
        mock_send_mail.assert_called_with(mail_dict)
