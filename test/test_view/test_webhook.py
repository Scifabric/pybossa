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


from helper import web
from default import with_context
from factories import ProjectFactory
from pybossa.core import user_repo

class TestWebhookView(web.Helper):

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
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        self.signout()
        res = self.register(name="juan")
        url = "/project/%s/webhook" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code

    @with_context
    def test_webhook_handler_owner(self):
        """Test WEBHOOK view works for owner."""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        url = "/project/%s/webhook" % project.short_name
        res = self.app.get(url)
        assert res.status_code == 200, res.status_code
        assert "Created" in res.data
        assert "Payload" in res.data
