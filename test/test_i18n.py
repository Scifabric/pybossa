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

from helper import web
from base import model, db, Fixtures


class TestI18n(web.Helper):
    def setUp(self):
        super(TestI18n, self).setUp()
        Fixtures.create()

    # Tests

    def test_00_i18n_anonymous(self):
        """Test i18n anonymous works"""
        # First default 'en' locale
        with self.app as c:
            err_msg = "The page should be in English"
            res = c.get('/', headers=[('Accept-Language', 'en')])
            assert "Community" in res.data, err_msg
        # Second with 'es' locale
        with self.app as c:
            err_msg = "The page should be in Spanish"
            res = c.get('/', headers=[('Accept-Language', 'es')])
            assert "Comunidad" in res.data, err_msg

    def test_01_i18n_authenticated(self):
        """Test i18n as an authenticated user works"""
        with self.app as c:
            # First default 'en' locale
            err_msg = "The page should be in English"
            res = c.get('/', follow_redirects=True)
            assert "Community" in res.data, err_msg
            self.register()
            self.signin()
            # After signing in it should be in English
            err_msg = "The page should be in English"
            res = c.get('/', follow_redirects=True)
            assert "Community" in res.data, err_msg

            # Change it to Spanish
            user = db.session.query(model.user.User).filter_by(name='johndoe').first()
            user.locale = 'es'
            db.session.add(user)
            db.session.commit()

            res = c.get('/', follow_redirects=True)
            err_msg = "The page should be in Spanish"
            assert "Comunidad" in res.data, err_msg
            # Sign out should revert it to English
            self.signout()
            err_msg = "The page should be in English"
            res = c.get('/', follow_redirects=True)
            assert "Community" in res.data, err_msg
