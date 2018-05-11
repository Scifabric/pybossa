# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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
from mock import patch


class TestHealthcheckView(web.Helper):

    @with_context
    def test_healthcheck(self):
        """Test healthcheck works during test"""
        url = "/diagnostics/healthcheck"
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code

    @with_context
    @patch('pybossa.view.diagnostics.sentinel.slave')
    def test_fail_healtcheck(self, slave):
        slave.ping.side_effect = Exception
        url = "/diagnostics/healthcheck"
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 500, res.status_code
        json_res = json.loads(res.data)
        assert not json_res['redis_slave']
        assert json_res['redis_master']
