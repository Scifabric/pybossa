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
from default import Test, flask_app, with_context
from pybossa.util import get_port
from pybossa.core import url_for_other_page
from mock import patch


class TestWebModule(Test):
    def setUp(self):
        super(TestWebModule, self).setUp()
        with self.flask_app.app_context():
            self.create()

    def test_url_for_other_page(self):
        """Test url_for_other page works."""
        with self.flask_app.test_request_context('/'):
            for i in range(1, 3):
                url = url_for_other_page(i)
                tmp = '/?page=%s' % i
                err_msg = "The page url is not built correctly"
                assert tmp == url, err_msg

    @with_context
    def test_get_port(self):
        """Test get_port works."""
        # Without os.environ
        err_msg = "It should return the default Flask port"
        with patch.dict(flask_app.config, {'PORT': 5000}):
            assert get_port() == 5000, err_msg
        with patch('os.environ.get', return_value='99'):
            err_msg = "The returning port should be 99"
            assert get_port() == 99, err_msg
