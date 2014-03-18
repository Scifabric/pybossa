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
from base import web, model, Fixtures, db, redis_flushall
import pybossa.view.twitter as twitter


class TestTwitter:
    def setUp(self):
        self.app = web.app
        model.rebuild_db()
        Fixtures.create()

    def tearDown(self):
        db.session.remove()
        redis_flushall()

    def test_manage_user(self):
        """Test TWITTER manage_user works."""
        with self.app.test_request_context('/'):
            # First with a new user
            user_data = dict(user_id=1, screen_name='twitter')
            token = dict(oauth_token='token', oauth_token_secret='secret')
            user = twitter.manage_user(token, user_data, None)
            assert user.email_addr == user_data['screen_name'], user
            assert user.name == user_data['screen_name'], user
            assert user.fullname == user_data['screen_name'], user
            assert user.twitter_user_id == user_data['user_id'], user

            # Second with the same user
            user = twitter.manage_user(token, user_data, None)
            assert user.email_addr == user_data['screen_name'], user
            assert user.name == user_data['screen_name'], user
            assert user.fullname == user_data['screen_name'], user
            assert user.twitter_user_id == user_data['user_id'], user

            # Finally with a user that already is in the system
            user_data = dict(user_id=10, screen_name=Fixtures.name)
            token = dict(oauth_token='token2', oauth_token_secret='secret2')
            user = twitter.manage_user(token, user_data, None)
            assert user is None
