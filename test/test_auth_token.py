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

from base import web, model, Fixtures, db
from pybossa.auth import token as token_authorization


class FakeCurrentUser:
    def __init__(self, user=None):
        if user:
            self.id = user.id
            self.admin = user.admin
        self.anonymous = user is None

    def is_anonymous(self):
        return self.anonymous

class TestTokenAuthorization:

    auth_providers = ('twitter', 'facebook', 'google')
    root, user1, user2 = Fixtures.create_users()


    def test_anonymous_user_delete(self):
        token_authorization.current_user = FakeCurrentUser()

        for token in self.auth_providers:
            assert not token_authorization.delete(token)

    def test_authenticated_user_delete(self):
        token_authorization.current_user = FakeCurrentUser(self.root)

        for token in self.auth_providers:
            assert not token_authorization.delete(token)

    def test_anonymous_user_create(self):
        token_authorization.current_user = FakeCurrentUser()

        for token in self.auth_providers:
            assert not token_authorization.create(token)

    def test_authenticated_user_create(self):
        token_authorization.current_user = FakeCurrentUser(self.root)

        for token in self.auth_providers:
            assert not token_authorization.create(token)

    def test_anonymous_user_update(self):
        token_authorization.current_user = FakeCurrentUser()

        for token in self.auth_providers:
            assert not token_authorization.update(token)

    def test_authenticated_user_update(self):
        token_authorization.current_user = FakeCurrentUser(self.root)

        for token in self.auth_providers:
            assert not token_authorization.update(token)

    def test_anonymous_user_read(self):
        token_authorization.current_user = FakeCurrentUser()

        for token in self.auth_providers:
            assert not token_authorization.read(token)

    def test_authenticated_user_read(self):
        token_authorization.current_user = FakeCurrentUser(self.root)

        for token in self.auth_providers:
            assert token_authorization.read(token)
