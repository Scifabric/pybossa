# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2016 SciFabric LTD.
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

from mock import patch
from flask import Response
from default import flask_app

class TestAmazonOAuth(object):

    @patch('pybossa.view.amazon.amazon.oauth')
    def test_amazon_login_converts_next_param_to_state_param(self, mock_oauth):
        mock_oauth.authorize.return_value = Response(302)
        next_url = 'http://server/project/myproject/tasks/import'
        flask_app.test_client().get('/amazon/?next=%s' % next_url)
        mock_oauth.authorize.assert_called_with(
            callback='http://localhost/amazon/oauth-authorized',
            state=next_url)
