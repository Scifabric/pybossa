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

from base import model, db
from nose.tools import assert_raises
from sqlalchemy.exc import IntegrityError


class TestModelUser:

    def setUp(self):
        model.rebuild_db()

    def tearDown(self):
        db.session.remove()



    def test_user(self):
        """Test USER model."""
        # First user
        user = model.User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            locale="en")

        user2 = model.User(
            email_addr="john.doe2@example.com",
            name="johndoe2",
            fullname="John Doe2",
            locale="en",)

        db.session.add(user)
        db.session.commit()
        tmp = db.session.query(model.User).get(1)
        assert tmp.email_addr == user.email_addr, tmp
        assert tmp.name == user.name, tmp
        assert tmp.fullname == user.fullname, tmp
        assert tmp.locale == user.locale, tmp
        assert tmp.api_key is not None, tmp
        assert tmp.created is not None, tmp
        err_msg = "First user should be admin"
        assert tmp.admin is True, err_msg
        err_msg = "check_password method should return False"
        assert tmp.check_password(password="nothing") is False, err_msg

        db.session.add(user2)
        db.session.commit()
        tmp = db.session.query(model.User).get(2)
        assert tmp.email_addr == user2.email_addr, tmp
        assert tmp.name == user2.name, tmp
        assert tmp.fullname == user2.fullname, tmp
        assert tmp.locale == user2.locale, tmp
        assert tmp.api_key is not None, tmp
        assert tmp.created is not None, tmp
        err_msg = "Second user should be not an admin"
        assert tmp.admin is False, err_msg

    def test_user_errors(self):
        """Test USER model errors."""
        user = model.User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            locale="en")

        # User.name should not be nullable
        user.name = None
        db.session.add(user)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # User.fullname should not be nullable
        user.name = "johndoe"
        user.fullname = None
        db.session.add(user)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # User.email_addr should not be nullable
        user.name = "johndoe"
        user.fullname = "John Doe"
        user.email_addr = None
        db.session.add(user)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()
