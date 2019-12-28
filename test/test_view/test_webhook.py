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
from helper import web
from default import with_context
from factories import ProjectFactory, TaskFactory, AnonymousTaskRunFactory
from pybossa.core import user_repo, webhook_repo
from pybossa.model import make_timestamp
from pybossa.model.webhook import Webhook
from pybossa.jobs import webhook
from mock import patch, call

class TestWebhookView(web.Helper):

    def payload(self, project, task):
        return dict(fired_at=make_timestamp(),
                    project_short_name=project.short_name,
                    project_id= project.id,
                    event='task_completed',
                    task_id=task.id)

    @with_context
    def test_webhook_handler_anon(self):
        """Test WEBHOOK view works for anons."""
        project = ProjectFactory.create()
        url = "/project/%s/webhook" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        assert "Sign in" in str(res.data), res.data

    @with_context
    def test_webhook_handler_auth(self):
        """Test WEBHOOK view works for authenticated not owner."""
        # Admin
        self.register()
        self.signout()
        # Owner
        self.register()
        owner = user_repo.get(1)
        project = ProjectFactory.create(owner=owner)
        self.signout()
        # User
        self.register(name="juan")
        url = "/project/%s/webhook" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code
        url = "/project/%s/webhook?all=true" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code
        url = "/project/%s/webhook?failed=true" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code


    @with_context
    def test_webhook_handler_owner_non_pro(self):
        """Test WEBHOOK view works for non pro owner."""
        # Admin
        self.register()
        self.signout()
        # User
        self.register(name="Iser")
        owner = user_repo.get_by(name="Iser")
        project = ProjectFactory.create(owner=owner)
        url = "/project/%s/webhook" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code
        url = "/project/%s/webhook?all=true" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code
        url = "/project/%s/webhook?failed=true" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code

    @with_context
    def test_webhook_handler_owner_pro(self):
        """Test WEBHOOK view works for pro owner."""
        # Admin/owner
        self.register()
        self.signout()
        # User
        self.register(name="Iser")
        owner = user_repo.get_by(name="Iser")
        owner.pro = True
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner)
        url = "/project/%s/webhook" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 200, res.status_code
        assert "Created" in str(res.data)
        assert "Payload" in str(res.data)
        url = "/project/%s/webhook?failed=true" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 200, res.status_code
        assert "Created" in str(res.data)
        assert "Payload" in str(res.data)
        url = "/project/%s/webhook?all=true" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 200, res.status_code
        assert "Created" in str(res.data)
        assert "Payload" in str(res.data)

    @with_context
    def test_webhook_handler_admin(self):
        """Test WEBHOOK view works for admin."""
        # Admin
        self.register()
        self.signout()
        # User
        self.register(name="user", password="user")
        owner = user_repo.get(2)
        self.signout()
        # Access as admin
        self.signin()
        project = ProjectFactory.create(owner=owner)
        url = "/project/%s/webhook" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 200, res.status_code
        assert "Created" in str(res.data)
        assert "Payload" in str(res.data)
        url = "/project/%s/webhook?all=true" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 200, res.status_code
        assert "Created" in str(res.data)
        assert "Payload" in str(res.data)
        url = "/project/%s/webhook?failed=true" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 200, res.status_code
        assert "Created" in str(res.data)
        assert "Payload" in str(res.data)

    @with_context
    def test_webhook_handler_post_oid(self):
        """Test WEBHOOK post oid works."""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project, n_answers=1)
        AnonymousTaskRunFactory.create(project=project, task=task)
        payload = self.payload(project, task)
        webhook = Webhook(project_id=project.id, payload=payload,
                          response='OK', response_status_code=200)
        webhook_repo.save(webhook)
        webhook = webhook_repo.get(1)
        url = "/project/%s/webhook/%s" % (project.short_name, webhook.id)
        res = self.app.post(url)
        tmp = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        assert tmp['payload']['project_short_name'] == project.short_name
        assert tmp['payload']['project_id'] == project.id
        assert tmp['payload']['task_id'] == task.id

    @with_context
    def test_webhook_handler_post_oid_404(self):
        """Test WEBHOOK post oid 404 works."""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project, n_answers=1)
        AnonymousTaskRunFactory.create(project=project, task=task)
        payload = self.payload(project, task)
        webhook = Webhook(project_id=project.id, payload=payload,
                          response='OK', response_status_code=200)
        webhook_repo.save(webhook)
        url = "/project/%s/webhook/%s" % (project.short_name, 9999)
        res = self.app.post(url)
        assert res.status_code == 404, res.status_code

    @with_context
    @patch('pybossa.view.projects.webhook_queue.enqueue')
    def test_webhook_handler_failed(self, q):
        """Test WEBHOOK requeing failed works."""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user, webhook='server')
        task = TaskFactory.create(project=project, n_answers=1)
        AnonymousTaskRunFactory.create(project=project, task=task)
        payload = self.payload(project, task)
        wh = Webhook(project_id=project.id, payload=payload,
                     response='error', response_status_code=500)
        webhook_repo.save(wh)
        wh2 = Webhook(project_id=project.id, payload=payload,
                      response='ok', response_status_code=200)
        webhook_repo.save(wh2)
        wh3 = Webhook(project_id=project.id, payload=payload,
                      response='ok', response_status_code=200)
        webhook_repo.save(wh3)

        wh = webhook_repo.get(1)
        url = "/project/%s/webhook?failed=true" % (project.short_name)
        res = self.app.get(url)
        assert res.status_code == 200, res.status_code
        q.assert_called_once_with(webhook, project.webhook,
                                  wh.payload, wh.id, True)

    @with_context
    @patch('pybossa.view.projects.webhook_queue.enqueue')
    def test_webhook_handler_all(self, q):
        """Test WEBHOOK requeing all works."""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user, webhook='server')
        task = TaskFactory.create(project=project, n_answers=1)
        AnonymousTaskRunFactory.create(project=project, task=task)
        payload = self.payload(project, task)
        wh1 = Webhook(project_id=project.id, payload=payload,
                     response='error', response_status_code=500)
        webhook_repo.save(wh1)
        wh2 = Webhook(project_id=project.id, payload=payload,
                      response='ok', response_status_code=200)
        webhook_repo.save(wh2)
        wh3 = Webhook(project_id=project.id, payload=payload,
                      response='ok', response_status_code=200)
        webhook_repo.save(wh3)
        whs = webhook_repo.filter_by(project_id=project.id)
        url = "/project/%s/webhook?all=true" % (project.short_name)
        res = self.app.get(url)
        assert res.status_code == 200, res.status_code
        calls = []
        for w in whs:
            calls.append(call(webhook, project.webhook,
                              w.payload, w.id, True))
        q.assert_has_calls(calls)
