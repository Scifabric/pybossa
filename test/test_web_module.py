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
from pybossa.web import url_for_other_page


class TestWebModule:
    def setUp(self):
        self.app = web.app
        model.rebuild_db()
        Fixtures.create()

    def test_url_for_other_page(self):
        """Test url_for_other page works."""
        with self.app.test_request_context('/'):
            for i in range(1, 3):
                url = url_for_other_page(i)
                tmp = '/?page=%s' % i
                err_msg = "The page url is not built correctly"
                assert tmp == url, err_msg
