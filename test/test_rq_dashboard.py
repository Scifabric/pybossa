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

from default import db, Fixtures, with_context
from helper import web
from mock import patch, Mock


class TestRQDashboard(web.Helper):

    @with_context
    def test_anonymous_user_gets_unauthorized(self):
        res = self.app.get('/admin/rq', follow_redirects=True)

        assert res.status_code == 401, res

    @with_context
    def test_non_admin_user_gets_forbidden(self):
        self.register()
        self.signout()
        self.register(fullname="jane", name="jane", email="jane@jane.com")
        res = self.app.get('/admin/rq', follow_redirects=True)

        assert res.status_code == 403, res

    @with_context
    def test_admin_user_can_access_dashboard(self):
        self.register()
        res = self.app.get('/admin/rq', follow_redirects=True)

        assert res.status_code == 200, res
