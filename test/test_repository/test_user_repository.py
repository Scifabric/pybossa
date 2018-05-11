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
# Cache global variables for timeouts

from default import Test, db, with_context
from nose.tools import assert_raises
from factories import UserFactory, TaskRunFactory
from pybossa.repositories import UserRepository, TaskRepository
from pybossa.exc import WrongObjectError, DBIntegrityError



class TestUserRepository(Test):

    def setUp(self):
        super(TestUserRepository, self).setUp()
        self.user_repo = UserRepository(db)
        self.task_repo = TaskRepository(db)


    @with_context
    def test_get_return_none_if_no_user(self):
        """Test get method returns None if there is no user with the
        specified id"""

        user = self.user_repo.get(200)

        assert user is None, user


    @with_context
    def test_get_returns_user(self):
        """Test get method returns a user if exists"""

        user = UserFactory.create()

        retrieved_user = self.user_repo.get(user.id)

        assert user == retrieved_user, retrieved_user


    @with_context
    def test_get_by_name_return_none_if_no_user(self):
        """Test get_by_name returns None when a user with the specified
        name does not exist"""

        user = self.user_repo.get_by_name('thisuserdoesnotexist')

        assert user is None, user


    @with_context
    def test_get_by_name_returns_the_user(self):
        """Test get_by_name returns a user if exists"""

        user = UserFactory.create()

        retrieved_user = self.user_repo.get_by_name(user.name)

        assert user == retrieved_user, retrieved_user


    @with_context
    def test_get_by(self):
        """Test get_by returns a user with the specified attribute"""

        user = UserFactory.create(name='Jon Snow')

        retrieved_user = self.user_repo.get_by(name=user.name)

        assert user == retrieved_user, retrieved_user


    @with_context
    def test_get_by_returns_none_if_no_user(self):
        """Test get_by returns None if no user matches the query"""

        UserFactory.create(name='Tyrion Lannister')

        user = self.user_repo.get_by(name='no_name')

        assert user is None, user


    @with_context
    def get_all_returns_list_of_all_users(self):
        """Test get_all returns a list of all the existing users"""

        users = UserFactory.create_batch(3)

        retrieved_users = self.user_repo.get_all()

        assert isinstance(retrieved_users, list)
        assert len(retrieved_users) == len(users), retrieved_users
        for user in retrieved_users:
            assert user in users, user


    @with_context
    def test_filter_by_no_matches(self):
        """Test filter_by returns an empty list if no users match the query"""

        UserFactory.create(name='reek', fullname='Theon Greyjoy')

        retrieved_users = self.user_repo.filter_by(name='asha')

        assert isinstance(retrieved_users, list)
        assert len(retrieved_users) == 0, retrieved_users


    @with_context
    def test_filter_by_one_condition(self):
        """Test filter_by returns a list of users that meet the filtering
        condition"""

        UserFactory.create_batch(3, locale='es')
        should_be_missing = UserFactory.create(locale='fr')

        retrieved_users = self.user_repo.filter_by(locale='es')

        assert len(retrieved_users) == 3, retrieved_users
        assert should_be_missing not in retrieved_users, retrieved_users


    @with_context
    def test_filter_by_multiple_conditions(self):
        """Test filter_by supports multiple-condition queries"""

        UserFactory.create_batch(2, locale='es', privacy_mode=True)
        user = UserFactory.create(locale='es', privacy_mode=False)

        retrieved_users = self.user_repo.filter_by(locale='es',
                                                   privacy_mode=False)

        assert len(retrieved_users) == 1, retrieved_users
        assert user in retrieved_users, retrieved_users


    @with_context
    def test_filter_by_limit_offset(self):
        """Test that filter_by supports limit and offset options"""

        UserFactory.create_batch(4)
        all_users = self.user_repo.filter_by()

        first_two = self.user_repo.filter_by(limit=2)
        last_two = self.user_repo.filter_by(limit=2, offset=2)

        assert len(first_two) == 2, first_two
        assert len(last_two) == 2, last_two
        assert first_two == all_users[:2]
        assert last_two == all_users[2:]


    @with_context
    def test_search_by_name_returns_list(self):
        """Test search_by_name returns a list with search results"""

        search = self.user_repo.search_by_name('')

        assert isinstance(search, list), search.__class__


    @with_context
    def test_search_by_name(self):
        """Test search_by_name returns a list with the user if searching by
        either its name or fullname"""

        user = UserFactory.create(name='greenseer', fullname='Jojen Reed')

        search_by_name = self.user_repo.search_by_name('greenseer')
        search_by_fullname = self.user_repo.search_by_name('Jojen Reed')

        assert user in search_by_name, search_by_name
        assert user in search_by_fullname, search_by_fullname


    @with_context
    def test_search_by_name_capital_lower_letters(self):
        """Test search_by_name works the same with capital or lower letters"""

        user_capitals = UserFactory.create(name='JOJEN')
        user_lowers = UserFactory.create(name='meera')

        search_lower = self.user_repo.search_by_name('jojen')
        search_capital = self.user_repo.search_by_name('MEERA')

        assert user_capitals in search_lower, search_lower
        assert user_lowers in search_capital, search_capital


    @with_context
    def test_search_by_name_substrings(self):
        """Test search_by_name works when searching by a substring"""

        user = UserFactory.create(name='Hodor')

        search = self.user_repo.search_by_name('odo')

        assert user in search, search


    @with_context
    def test_search_by_name_empty_string(self):
        """Test search_by_name returns an empty list when searching by '' """

        user = UserFactory.create(name='Brandon')

        search = self.user_repo.search_by_name('')

        assert len(search) == 0, search


    @with_context
    def test_total_users_no_users(self):
        """Test total_users return 0 if there are no users"""

        count = self.user_repo.total_users()

        assert count == 0, count


    @with_context
    def test_total_users_count(self):
        """Test total_users return 1 if there is one user"""

        UserFactory.create()
        count = self.user_repo.total_users()

        assert count == 1, count


    @with_context
    def test_save(self):
        """Test save persist the user"""

        user = UserFactory.build()
        assert self.user_repo.get(user.id) is None

        self.user_repo.save(user)

        assert self.user_repo.get(user.id) == user, "User not saved"


    @with_context
    def test_save_fails_if_integrity_error(self):
        """Test save raises a DBIntegrityError if the instance to be saved lacks
        a required value"""

        user = UserFactory.build(name=None)

        assert_raises(DBIntegrityError, self.user_repo.save, user)


    @with_context
    def test_save_only_saves_users(self):
        """Test save raises a WrongObjectError when an object which is not
        a User instance is saved"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.user_repo.save, bad_object)


    @with_context
    def test_update(self):
        """Test update persists the changes made to the user"""

        user = UserFactory.create(locale='en')
        user.locale = 'it'

        self.user_repo.update(user)
        updated_user = self.user_repo.get(user.id)

        assert updated_user.locale == 'it', updated_user


    @with_context
    def test_update_fails_if_integrity_error(self):
        """Test update raises a DBIntegrityError if the instance to be updated
        lacks a required value"""

        user = UserFactory.create()
        user.name = None

        assert_raises(DBIntegrityError, self.user_repo.update, user)


    @with_context
    def test_update_only_updates_users(self):
        """Test update raises a WrongObjectError when an object which is not
        a User instance is updated"""

        bad_object = dict()

        assert_raises(WrongObjectError, self.user_repo.update, bad_object)


    @with_context
    def test_get_users_no_args(self):
        """Test get users by id returns empty list
        """
        assert self.user_repo.get_users(None) == []


    @with_context
    def test_get_users(self):

        tyrion = UserFactory.create(name='Tyrion Lannister')
        theon = UserFactory.create(name='reek', fullname='Theon Greyjoy')

        retrieved_users = self.user_repo.get_users([tyrion.id, theon.id])
        assert any(user == tyrion for user in retrieved_users)
        assert any(user == theon for user in retrieved_users)

    @with_context
    def test_delete_user(self):
        """Test USER delete works."""
        user = UserFactory.create()
        user_id = user.id
        user = self.user_repo.get_by(id=user_id)
        assert user.id == user_id
        self.user_repo.delete(user)
        user = self.user_repo.get_by(id=user_id)
        assert user is None

    @with_context
    def test_fake_user_id(self):
        """Test remove user ID works and it's replaced by a fake IP."""
        user = UserFactory.create()
        taskruns = TaskRunFactory.create_batch(3, user=user)
        fake_ips = []
        assert taskruns[0].user_id == user.id
        self.user_repo.fake_user_id(user)
        for taskrun in taskruns:
            taskrun = self.task_repo.get_task_run_by(id=taskrun.id)
            assert taskrun.user_id is None
            assert taskrun.user_ip is not None
            fake_ips.append(taskrun.user_ip)
        assert len(set(fake_ips)) == 3

    @with_context
    def test_delete_user_with_task_runs(self):
        """Delete user with task runs works."""
        user = UserFactory.create()
        taskruns = TaskRunFactory.create_batch(3, user=user)
        fake_ips = []
        user_id = user.id
        assert taskruns[0].user_id == user.id
        self.user_repo.delete(user)
        for taskrun in taskruns:
            taskrun = self.task_repo.get_task_run_by(id=taskrun.id)
            assert taskrun.user_id is None
            assert taskrun.user_ip is not None
            fake_ips.append(taskrun.user_ip)
        assert len(set(fake_ips)) == 3
        user = self.user_repo.get_by(id=user_id)
        assert user is None
