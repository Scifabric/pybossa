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
from helper import web
from default import with_context
from factories import ProjectFactory, TaskFactory, AnonymousTaskRunFactory
from pybossa.core import user_repo, webhook_repo
from pybossa.model import make_timestamp
from pybossa.model.webhook import Webhook

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
        assert "Sign in" in res.data, res.data

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
        assert "Created" in res.data
        assert "Payload" in res.data

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
        assert "Created" in res.data
        assert "Payload" in res.data

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
