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
from default import Test, db, with_context
from pybossa.view.facebook import manage_user
from pybossa.model.user import User


class TestFacebook(Test):
    def test_manage_user_with_email(self):
        """Test FACEBOOK manage_user works."""
        with self.flask_app.test_request_context('/'):
            # First with a new user
            user_data = dict(id=1, username='facebook',
                             email='f@f.com', name='name')
            token = 't'
            user = manage_user(token, user_data, None)
            assert user.email_addr == user_data['email'], user
            assert user.name == user_data['username'], user
            assert user.fullname == user_data['name'], user
            assert user.facebook_user_id == user_data['id'], user

            # Second with the same user
            user = manage_user(token, user_data, None)
            assert user.email_addr == user_data['email'], user
            assert user.name == user_data['username'], user
            assert user.fullname == user_data['name'], user
            assert user.facebook_user_id == user_data['id'], user

            # Finally with a user that already is in the system
            user_data = dict(id=10, username=self.name,
                             email=self.email_addr, name=self.fullname)
            token = 'tA'
            user = manage_user(token, user_data, None)
            assert user.facebook_user_id == 10, err_msg

    @with_context
    def test_manage_user_without_email(self):
        """Test FACEBOOK manage_user without e-mail works."""
        # First with a new user
        user_data = dict(id=1, username='facebook', name='name')
        token = 't'
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['username'], user
        assert user.fullname == user_data['name'], user
        assert user.facebook_user_id == user_data['id'], user

        # Second with the same user
        user = manage_user(token, user_data, None)
        assert user.email_addr == user_data['email'], user
        assert user.name == user_data['username'], user
        assert user.fullname == user_data['name'], user
        assert user.facebook_user_id == user_data['id'], user

        # Finally with a user that already is in the system
        user_data = dict(id=10, username=self.name,
                         email=self.email_addr, name=self.fullname)
        token = 'tA'
        user = manage_user(token, user_data, None)
        err_msg = "It should return the same user"
        assert user.facebook_user_id == 10, err_msg
