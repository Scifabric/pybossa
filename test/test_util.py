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
import pybossa.util
from base import web, model, Fixtures
from mock import patch


class TestWebModule:
    def setUp(self):
        #self.app = web.app
        self.app = web.app.test_client()
        model.rebuild_db()
        Fixtures.create()

    def test_jsonpify(self):
        """Test jsonpify decorator works."""
        res = self.app.get('/api/app/1?callback=mycallback')
        err_msg = "mycallback should be included in the response"
        assert "mycallback" in res.data, err_msg
        err_msg = "Status code should be 200"
        assert res.status_code == 200, err_msg

    def test_cors(self):
        """Test CORS decorator works."""
        res = self.app.get('/api/app/1')
        err_msg = "CORS should be enabled"
        print res.headers
        assert res.headers['Access-Control-Allow-Origin'] == '*', err_msg
        methods = 'PUT, HEAD, DELETE, OPTIONS, GET'
        assert res.headers['Access-Control-Allow-Methods'] == methods, err_msg
        assert res.headers['Access-Control-Max-Age'] == '21600', err_msg
        headers = 'CONTENT-TYPE, AUTHORIZATION'
        assert res.headers['Access-Control-Allow-Headers'] == headers, err_msg
