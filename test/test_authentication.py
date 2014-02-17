# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

from base import web, model, Fixtures


class TestAuthentication:
    @classmethod
    def setup_class(cls):
        cls.app = web.app.test_client()
        model.rebuild_db()
        Fixtures.create()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    def test_api_authenticate(self):
        """Test AUTHENTICATION works"""
        res = self.app.get('/?api_key=%s' % Fixtures.api_key)
        assert 'checkpoint::logged-in::tester' in res.data, res.data
