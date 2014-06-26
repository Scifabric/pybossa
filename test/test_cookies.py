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

from pybossa.cookies import CookieHandler
from mock import MagicMock


class TestCookieHandler(object):

    def test_cookie_handler_adds_cookie_to_response(self):
        """Test that a CookieHandler object can successfully add a cookie to a
        response object"""
        mock_signer = MagicMock()
        mock_signer.loads = lambda x: x
        mock_signer.dumps = lambda x: x
        mock_request = MagicMock(cookies={})
        mock_response = MagicMock()
        project = MagicMock(short_name='my_project')
        user = 'someone'
        cookie_handler = CookieHandler(request=mock_request, signer=mock_signer)

        cookie_handler.add_cookie_to(mock_response, project, user)

        mock_response.set_cookie.assert_called_with('my_projectpswd',
                                                    [user], max_age=1200)

    def test_cookie_habdler_updates_cookie(self):
        """Test that a CookieHandler updates the cookie with another user's info"""
        mock_signer = MagicMock()
        mock_signer.loads = lambda x: x
        mock_signer.dumps = lambda x: x
        mock_request = MagicMock(cookies={'my_projectpswd': ['first_user']})
        mock_response = MagicMock()
        project = MagicMock(short_name='my_project')
        user = 'second_user'
        cookie_handler = CookieHandler(request=mock_request, signer=mock_signer)

        cookie_handler.add_cookie_to(mock_response, project, user)

        mock_response.set_cookie.assert_called_with('my_projectpswd',
                                                    ['first_user', user],
                                                    max_age=1200)






