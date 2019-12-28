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

from helper import web
from default import db

from pybossa.repositories import UserRepository
user_repo = UserRepository(db)


class TestI18n(web.Helper):
    def setUp(self):
        super(TestI18n, self).setUp()
        with self.flask_app.app_context():
            self.create()

    # Tests
    def test_00_i18n_anonymous(self):
        """Test i18n anonymous works"""
        # First default 'en' locale
        err_msg = "The page should be in English"
        res = self.app.get('/')
        assert "Community" in str(res.data), err_msg

        self.app.set_cookie('localhost', 'language', 'RU')
        err_msg = "The page should be in English"
        res = self.app.get('/')
        assert "Community" in str(res.data), err_msg

        # Second with 'es' locale
        self.app.set_cookie('localhost', 'language', 'ES')
        err_msg = "The page should be in Spanish"
        res = self.app.get('/')
        assert "Comunidad" in str(res.data), err_msg

    def test_01_i18n_authenticated(self):
        """Test i18n as an authenticated user works"""
        # First default 'en' locale
        err_msg = "The page should be in English"
        res = self.app.get('/', follow_redirects=True)
        assert "Community" in str(res.data), err_msg
        self.register()
        self.signin()
        # After signing in it should be in English
        err_msg = "The page should be in English"
        res = self.app.get('/', follow_redirects=True)
        assert "Community" in str(res.data), err_msg

        # Change it to Spanish
        user = user_repo.get_by_name('johndoe')
        user.locale = 'es'
        user_repo.update(user)

        res = self.app.get('/', follow_redirects=True)
        err_msg = "The page should be in Spanish"
        assert "Comunidad" in str(res.data), err_msg
        # Sign out should revert it to English
        self.signout()
        err_msg = "The page should be in English"
        res = self.app.get('/', follow_redirects=True)
        assert "Community" in str(res.data), err_msg
