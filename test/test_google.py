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
from default import Test, with_context
from pybossa.view.google import manage_user


class TestGoogle(Test):
    @with_context
    def test_manage_user(self):
        """Test GOOGLE manage_user works."""
        # First with a new user
        user_data = dict(id='1', name='google',
                         email='g@g.com')
        token = 't'
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['name'], user
        assert user.fullname == user_data['name'], user
        assert user.google_user_id == user_data['id'], user

        # Second with the same user
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['name'], user
        assert user.fullname == user_data['name'], user
        assert user.google_user_id == user_data['id'], user

        # Finally with a user that already is in the system
        user_data = dict(id='10', name=self.name,
                         email=self.email_addr)
        token = 'tA'
        user = manage_user(token, user_data, None)
        err_msg = "User should be the same"
        print user.google_user_id
        assert user.google_user_id == '10', err_msg
