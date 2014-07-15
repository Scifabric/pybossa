# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
# Cache global variables for timeouts

from default import Test, db
from nose.tools import assert_raises
from factories import UserFactory
from pybossa.repositories import UserRepository
from pybossa.exc import WrongObjectError, DBIntegrityError



class TestUserRepository(Test):

    def setUp(self):
        super(TestUserRepository, self).setUp()
        self.user_repo = UserRepository(db)


    def test_get_return_none_if_no_user(self):
        """Test get method returns None if there is no user with the
        specified id"""

        user = self.user_repo.get(200)

        assert user is None, user


    def test_get_returns_user(self):
        """Test get method returns a user if exists"""

        user = UserFactory.create()

        retrieved_user = self.user_repo.get(user.id)

        assert user == retrieved_user, retrieved_user


    def test_get_by_name_return_none_if_no_user(self):
        """Test get_by_name returns None when a user with the specified
        name does not exist"""

        user = self.user_repo.get_by_name('thisuserdoesnotexist')

        assert user is None, user


    def test_get_by_name_returns_the_user(self):
        """Test get_by_name returns a user if exists"""

        user = UserFactory.create()

        retrieved_user = self.user_repo.get_by_name(user.name)

        assert user == retrieved_user, retrieved_user


    def test_get_by(self):
        """Test get_by returns a user with the specified attribute"""

        user = UserFactory.create(name='Jon Snow')

        retrieved_user = self.user_repo.get_by(name=user.name)

        assert user == retrieved_user, retrieved_user


    def test_get_by_returns_none_if_no_user(self):
        """Test get_by returns None if no user matches the query"""

        UserFactory.create(name='Tyrion Lannister')

        user = self.user_repo.get_by(name='no_name')

        assert user is None, user


    def get_all_returns_list_of_all_users(self):
        """Test get_all returns a list of all the existing users"""

        users = UserFactory.create_batch(3)

        retrieved_users = self.user_repo.get_all()

        assert isinstance(retrieved_users, list)
        assert len(retrieved_users) == len(users), retrieved_users
        for user in retrieved_users:
            assert user in users, user


    def test_filter_by_no_matches(self):
        """Test filter_by returns an empty list if no users match the query"""

        UserFactory.create(name='reek', fullname='Theon Greyjoy')

        retrieved_users = self.user_repo.filter_by(name='asha')

        assert isinstance(retrieved_users, list)
        assert len(retrieved_users) == 0, retrieved_users


    def test_filter_by_one_condition(self):
        """Test filter_by returns a list of users that meet the filtering
        condition"""

        UserFactory.create_batch(3, locale='es')
        should_be_missing = UserFactory.create(locale='fr')

        retrieved_users = self.user_repo.filter_by(locale='es')

        assert len(retrieved_users) == 3, retrieved_users
        assert should_be_missing not in retrieved_users, retrieved_users


    def test_filter_by_multiple_conditions(self):
        """Test filter_by supports multiple-condition queries"""

        UserFactory.create_batch(2, locale='es', privacy_mode=True)
        user = UserFactory.create(locale='es', privacy_mode=False)

        retrieved_users = self.user_repo.filter_by(locale='es',
                                                   privacy_mode=False)

        assert len(retrieved_users) == 1, retrieved_users
        assert user in retrieved_users, retrieved_users

