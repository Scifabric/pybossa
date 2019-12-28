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

from default import Test, db, with_context
from nose.tools import assert_raises
from sqlalchemy.exc import IntegrityError
from pybossa.model.user import User


class TestModelUser(Test):

    @with_context
    def test_user(self):
        """Test USER model."""
        # First user
        user = User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            locale="en")

        user2 = User(
            email_addr="john.doe2@example.com",
            name="johndoe2",
            fullname="John Doe2",
            locale="en",)

        db.session.add(user)
        db.session.commit()
        tmp = db.session.query(User).get(1)
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
        tmp = db.session.query(User).get(2)
        assert tmp.email_addr == user2.email_addr, tmp
        assert tmp.name == user2.name, tmp
        assert tmp.fullname == user2.fullname, tmp
        assert tmp.locale == user2.locale, tmp
        assert tmp.api_key is not None, tmp
        assert tmp.created is not None, tmp
        err_msg = "Second user should be not an admin"
        assert tmp.admin is False, err_msg

    @with_context
    def test_user_errors(self):
        """Test USER model errors."""
        user = User(
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

    @with_context
    def test_user_public_attributes(self):
        """Test public attributes works."""
        user = User(
            email_addr="john.doe@example.com",
            name="johndoe",
            pro=1,
            fullname="John Doe",
            locale="en")
        public_attributes = ['created', 'name', 'fullname', 'locale', 'info',
                             'n_answers', 
                             'registered_ago', 'rank', 'score']

        user.set_password("juandiso")
        print(sorted(public_attributes))
        print(sorted(user.public_attributes()))
        assert sorted(public_attributes) == sorted(user.public_attributes())
        data = user.to_public_json()
        err_msg = "There are some keys that should not be public"
        assert sorted(list(data.keys())) == sorted(public_attributes), err_msg
        all_attributes = list(user.dictize().keys())
        s = set(public_attributes)
        private_attributes = [x for x in all_attributes if x not in s]
        for attr in private_attributes:
            err_msg = "This attribute should be private %s" % attr
            assert data.get(attr) is None, err_msg

    @with_context
    def test_user_public_info_keys(self):
        """Test public info keys works."""
        user = User(
            email_addr="john.doe@example.com",
            name="johndoe",
            fullname="John Doe",
            info=dict(avatar='image.png', container='foldr3', token='security'),
            locale="en")
        public_info_keys = ['avatar', 'container']
        user.set_password("juandiso")
        assert public_info_keys.sort() == user.public_info_keys().sort()

        data = user.to_public_json()
        err_msg = "There are some keys that should not be public"
        assert list(data.get('info').keys()).sort() == public_info_keys.sort(), err_msg
