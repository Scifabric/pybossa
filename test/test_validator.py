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
import pybossa.validator
from pybossa.view.account import LoginForm
from flaskext.wtf import ValidationError
from nose.tools import raises


class TestValidator:
    def setUp(self):
        self.app = web.app
        model.rebuild_db()
        Fixtures.create()

    def tearDown(self):
        db.session.remove()
        redis_flushall()

    @raises(ValidationError)
    def test_unique(self):
        """Test VALIDATOR Unique works."""
        with self.app.test_request_context('/'):
            f = LoginForm()
            f.email.data = Fixtures.email_addr
            u = pybossa.validator.Unique(db.session, model.User,
                                         model.User.email_addr)
            u.__call__(f, f.email)

    @raises(ValidationError)
    def test_not_allowed_chars(self):
        """Test VALIDATOR NotAllowedChars works."""
        with self.app.test_request_context('/'):
            f = LoginForm()
            f.email.data = Fixtures.email_addr + "$"
            u = pybossa.validator.NotAllowedChars()
            u.__call__(f, f.email)

    @raises(ValidationError)
    def test_comma_separated_integers(self):
        """Test VALIDATOR CommaSeparatedIntegers works."""
        with self.app.test_request_context('/'):
            f = LoginForm()
            f.email.data = '1 2 3'
            u = pybossa.validator.CommaSeparatedIntegers()
            u.__call__(f, f.email)
