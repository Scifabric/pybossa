# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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

from default import Test, with_context
from pybossa.cache import users as cached_users
from pybossa.model.user import User
from pybossa.leaderboard.jobs import leaderboard as update_leaderboard

from factories import ProjectFactory, TaskFactory, TaskRunFactory, UserFactory


class TestUsersCache(Test):

    @with_context
    def test_get_user_summary_nousers(self):
        """Test CACHE USERS get_user_summary returns None if no user exists with
        the name requested"""
        user = cached_users.get_user_summary('nouser')

        assert user is None, user

    @with_context
    def test_public_get_user_summary_nousers(self):
        """Test public CACHE USERS get_user_summary returns None if no user exists with
        the name requested"""
        user = cached_users.public_get_user_summary('nouser')

        assert user is None, user

    @with_context
    def test_get_user_summary_user_exists(self):
        """Test CACHE USERS get_user_summary returns a dict with the user data
        if the user exists"""
        UserFactory.create(name='zidane')
        UserFactory.create(name='figo')

        zizou = cached_users.get_user_summary('zidane')

        assert type(zizou) is dict, type(zizou)
        assert zizou != None, zizou

    @with_context
    def test_public_get_user_summary_user_exists(self):
        """Test public CACHE USERS get_user_summary returns a dict with the user data
        if the user exists"""
        UserFactory.create(name='zidane')
        UserFactory.create(name='figo')

        zizou = cached_users.public_get_user_summary('zidane')

        assert type(zizou) is dict, type(zizou)
        assert zizou != None, zizou

    @with_context
    def test_get_user_summary_returns_fields(self):
        """Test CACHE USERS get_user_summary all the fields in the dict"""
        UserFactory.create(name='user')
        fields = ('id', 'name', 'fullname', 'created', 'api_key',
                  'twitter_user_id', 'google_user_id', 'facebook_user_id',
                  'info', 'admin', 'email_addr', 'n_answers', 'rank', 'score',
                  'total')
        user = cached_users.get_user_summary('user')

        for field in fields:
            assert field in list(user.keys()), field

    @with_context
    def test_public_get_user_summary_returns_fields(self):
        """Test CACHE USERS public_get_user_summary all the fields in the dict"""
        UserFactory.create(name='user')
        public_fields = ('name', 'info', 'fullname', 'created', 'rank', 'score')
        private_fields = ('id', 'api_key', 'twitter_user_id', 'google_user_id',
                          'facebook_user_id', 'admin', 'email_addr', 'total')
        user = cached_users.public_get_user_summary('user')

        for field in public_fields:
            assert field in list(user.keys()), field

        for field in private_fields:
            assert field not in list(user.keys()), field

    @with_context
    def test_rank_and_score(self):
        """Test CACHE USERS rank_and_score returns the correct rank and score"""
        i = 0
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(4, project=project)
        users = UserFactory.create_batch(4)
        for user in users:
            i += 1
            taskruns = TaskRunFactory.create_batch(i, user=user, task=tasks[i - 1])

        update_leaderboard()
        first_in_rank = cached_users.rank_and_score(users[3].id)
        last_in_rank = cached_users.rank_and_score(users[0].id)
        print(first_in_rank)
        assert first_in_rank['rank'] == 1, first_in_rank['rank']
        assert first_in_rank['score'] == 4, first_in_rank['score']
        assert last_in_rank['rank'] == 4, last_in_rank['rank']
        assert last_in_rank['score'] == 1, last_in_rank['score']

    @with_context
    def test_projects_contributed_no_contributions(self):
        """Test CACHE USERS projects_contributed returns empty list if the user has
        not contributed to any project"""
        user = UserFactory.create()

        projects_contributed = cached_users.projects_contributed(user.id)

        assert projects_contributed == [], projects_contributed

    @with_context
    def test_projects_contributed_no_contributions_cached(self):
        """Test CACHE USERS projects_contributed_cached returns empty list if the user has
        not contributed to any project"""
        user = UserFactory.create()

        projects_contributed = cached_users.projects_contributed_cached(user.id)

        assert projects_contributed == [], projects_contributed

    @with_context
    def test_public_projects_contributed_no_contributions(self):
        """Test public CACHE USERS projects_contributed returns empty list if the user has
        not contributed to any project"""
        user = UserFactory.create()

        projects_contributed = cached_users.public_projects_contributed(user.id)

        assert projects_contributed == [], projects_contributed

    @with_context
    def test_public_projects_contributed_no_contributions_cached(self):
        """Test public CACHE USERS projects_contributed_cached returns empty list if the user has
        not contributed to any project"""
        user = UserFactory.create()

        projects_contributed = cached_users.public_projects_contributed_cached(user.id)

        assert projects_contributed == [], projects_contributed

    @with_context
    def test_projects_contributed_contributions(self):
        """Test CACHE USERS projects_contributed returns a list of projects that has
        contributed to"""
        user = UserFactory.create()
        project_contributed = ProjectFactory.create()
        task = TaskFactory.create(project=project_contributed)
        TaskRunFactory.create(task=task, user=user)
        another_project = ProjectFactory.create()

        projects_contributed = cached_users.projects_contributed(user.id)

        assert len(projects_contributed) == 1
        assert projects_contributed[0]['short_name'] == project_contributed.short_name, projects_contributed

    @with_context
    def test_projects_contributed_contributions_cached(self):
        """Test CACHE USERS projects_contributed_cached returns a list of projects that has
        contributed to"""
        user = UserFactory.create()
        project_contributed = ProjectFactory.create()
        task = TaskFactory.create(project=project_contributed)
        TaskRunFactory.create(task=task, user=user)
        another_project = ProjectFactory.create()

        projects_contributed = cached_users.projects_contributed_cached(user.id)

        assert len(projects_contributed) == 1
        assert projects_contributed[0]['short_name'] == project_contributed.short_name, projects_contributed

    @with_context
    def test_public_projects_contributed_contributions(self):
        """Test CACHE USERS public projects_contributed returns a list of projects that has
        contributed to"""
        user = UserFactory.create()
        project_contributed = ProjectFactory.create()
        task = TaskFactory.create(project=project_contributed)
        TaskRunFactory.create(task=task, user=user)
        another_project = ProjectFactory.create()

        projects_contributed = cached_users.public_projects_contributed(user.id)

        assert len(projects_contributed) == 1
        assert projects_contributed[0]['short_name'] == project_contributed.short_name, projects_contributed

        # check privacy
        err_msg = 'private information is in public record'
        assert 'secret_key' not in projects_contributed[0], err_msg
        assert 'onesignal' not in projects_contributed[0]['info']
        assert 'passwd_hash' not in projects_contributed[0]['info']

    @with_context
    def test_public_projects_contributed_contributions_cached(self):
        """Test CACHE USERS public cached projects_contributed returns a list of projects that has
        contributed to"""
        user = UserFactory.create()
        project_contributed = ProjectFactory.create()
        task = TaskFactory.create(project=project_contributed)
        TaskRunFactory.create(task=task, user=user)
        another_project = ProjectFactory.create()

        projects_contributed = cached_users.public_projects_contributed_cached(user.id)

        assert len(projects_contributed) == 1
        assert projects_contributed[0]['short_name'] == project_contributed.short_name, projects_contributed

        # check privacy
        err_msg = 'private information is in public record'
        assert 'secret_key' not in projects_contributed[0], err_msg
        assert 'onesignal' not in projects_contributed[0]['info']
        assert 'passwd_hash' not in projects_contributed[0]['info']

    @with_context
    def test_projects_contributed_returns_fields(self):
        """Test CACHE USERS projects_contributed returns the info of the projects with
        the required fields"""
        user = UserFactory.create()
        project_contributed = ProjectFactory.create()
        task = TaskFactory.create(project=project_contributed)
        TaskRunFactory.create(task=task, user=user)
        fields = ('id', 'name', 'short_name', 'owner_id', 'description',
                  'overall_progress', 'n_tasks', 'n_volunteers', 'info')

        projects_contributed = cached_users.projects_contributed(user.id)

        for field in fields:
            assert field in list(projects_contributed[0].keys()), field

    @with_context
    def test_published_projects_no_projects(self):
        """Test CACHE USERS published_projects returns empty list if the user has
        not created any project"""
        user = UserFactory.create()

        projects_published = cached_users.published_projects(user.id)

        assert projects_published == [], projects_published

    @with_context
    def test_published_projects_no_projects_cached(self):
        """Test CACHE USERS published_projects_cached returns empty list if the user has
        not created any project"""
        user = UserFactory.create()

        projects_published = cached_users.published_projects_cached(user.id)

        assert projects_published == [], projects_published

    @with_context
    def test_public_published_projects_no_projects(self):
        """Test public CACHE USERS published_projects returns empty list if the user has
        not created any project"""
        user = UserFactory.create()

        projects_published = cached_users.public_published_projects(user.id)

        assert projects_published == [], projects_published

    @with_context
    def test_public_published_projects_no_projects_cached(self):
        """Test public CACHE USERS published_projects_cached returns empty list if the user has
        not created any project"""
        user = UserFactory.create()

        projects_published = cached_users.public_published_projects_cached(user.id)

        assert projects_published == [], projects_published

    @with_context
    def test_published_projects_returns_published(self):
        """Test CACHE USERS published_projects returns a list with the projects that
        are published by the user"""
        user = UserFactory.create()
        published_project = ProjectFactory.create(owner=user, published=True)

        projects_published = cached_users.published_projects(user.id)

        assert len(projects_published) == 1, projects_published
        assert projects_published[0]['short_name'] == published_project.short_name, projects_published

    @with_context
    def test_public_published_projects_returns_published(self):
        """Test public CACHE USERS published_projects returns a list with the projects that
        are published by the user"""
        user = UserFactory.create()
        published_project = ProjectFactory.create(owner=user, published=True)

        projects_published = cached_users.public_published_projects(user.id)

        assert len(projects_published) == 1, projects_published
        assert projects_published[0]['short_name'] == published_project.short_name, projects_published

    @with_context
    def test_published_projects_only_returns_published(self):
        """Test CACHE USERS published_projects does not return draft
        or another user's projects"""
        user = UserFactory.create()
        another_user_published_project = ProjectFactory.create(published=True)
        draft_project = ProjectFactory.create(owner=user, published=False)

        projects_published = cached_users.published_projects(user.id)

        assert len(projects_published) == 0, projects_published

    @with_context
    def test_published_projects_returns_fields(self):
        """Test CACHE USERS published_projects returns the info of the projects with
        the required fields"""
        user = UserFactory.create()
        published_project = ProjectFactory.create(owner=user, published=True)
        fields = ('id', 'name', 'short_name', 'owner_id', 'description',
                  'overall_progress', 'n_tasks', 'n_volunteers', 'info')

        projects_published = cached_users.published_projects(user.id)

        for field in fields:
            assert field in list(projects_published[0].keys()), field

    @with_context
    def test_public_published_projects_returns_fields(self):
        """Test CACHE USERS published_projects returns the info of the projects with
        the required fields"""
        user = UserFactory.create()
        published_project = ProjectFactory.create(owner=user, published=True)
        private_fields = ('owner_id')
        public_fields = ('name', 'short_name', 'description',
                         'overall_progress', 'n_tasks', 'n_volunteers', 'info')

        projects_published = cached_users.public_published_projects(user.id)

        for field in public_fields:
            assert field in list(projects_published[0].keys()), field

        for field in private_fields:
            assert field not in list(projects_published[0].keys()), field

    @with_context
    def test_public_published_projects_cached_returns_fields(self):
        """Test CACHE USERS published_projects_cached returns the info of the projects with
        the required fields"""
        user = UserFactory.create()
        published_project = ProjectFactory.create(owner=user, published=True)
        private_fields = ('owner_id')
        public_fields = ('name', 'short_name', 'description',
                         'overall_progress', 'n_tasks', 'n_volunteers', 'info')

        projects_published = cached_users.public_published_projects_cached(user.id)

        for field in public_fields:
            assert field in list(projects_published[0].keys()), field

        for field in private_fields:
            assert field not in list(projects_published[0].keys()), field

    @with_context
    def test_draft_projects_no_projects(self):
        """Test CACHE USERS draft_projects returns an empty list if the user has no
        draft projects"""
        user = UserFactory.create()
        published_project = ProjectFactory.create(owner=user, published=True)

        draft_projects = cached_users.draft_projects(user.id)

        assert len(draft_projects) == 0, draft_projects

    @with_context
    def test_draft_projects_return_drafts(self):
        """Test CACHE USERS draft_projects returns draft belonging to the user"""
        user = UserFactory.create()
        draft_project = ProjectFactory.create(owner=user, published=False)

        draft_projects = cached_users.draft_projects(user.id)

        assert len(draft_projects) == 1, draft_projects
        assert draft_projects[0]['short_name'] == draft_project.short_name, draft_projects

    @with_context
    def test_draft_projects_only_returns_drafts(self):
        """Test CACHE USERS draft_projects does not return any pubished projects
        or drafts that belong to another user"""
        user = UserFactory.create()
        published_project = ProjectFactory.create(owner=user, published=True)
        other_users_draft_project = ProjectFactory.create(published=False)

        draft_projects = cached_users.draft_projects(user.id)

        assert len(draft_projects) == 0, draft_projects

    @with_context
    def test_draft_projects_returns_fields(self):
        """Test CACHE USERS draft_projects returns the info of the projects with
        the required fields"""
        user = UserFactory.create()
        draft_project = ProjectFactory.create(owner=user, published=False)
        fields = ('id', 'name', 'short_name', 'owner_id', 'description',
                  'overall_progress', 'n_tasks', 'n_volunteers', 'info')

        draft_project = cached_users.draft_projects(user.id)

        for field in fields:
            assert field in list(draft_project[0].keys()), field

    @with_context
    def test_get_leaderboard_no_users_returns_empty_list(self):
        """Test CACHE USERS get_leaderboard returns an empty list if there are no
        users"""

        users = cached_users.get_leaderboard(10)

        assert users == [], users

    @with_context
    def test_get_leaderboard_returns_users_ordered_by_rank(self):
        leader = UserFactory.create()
        second = UserFactory.create()
        third = UserFactory.create()
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(3, project=project)
        i = 3
        for user in [leader, second, third]:
            TaskRunFactory.create_batch(i, user=user, task=tasks[i - 1])
            i -= 1

        update_leaderboard()
        leaderboard = cached_users.get_leaderboard(3)

        assert leaderboard[0]['name'] == leader.name
        assert leaderboard[1]['name'] == second.name
        assert leaderboard[2]['name'] == third.name

    @with_context
    def test_get_leaderboard_includes_specific_user_even_is_not_in_top(self):
        leader = UserFactory.create()
        second = UserFactory.create()
        third = UserFactory.create()
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(3, project=project)
        i = 3
        for user in [leader, second, third]:
            TaskRunFactory.create_batch(i, user=user, task=tasks[i - 1])
            i -= 1
        user_out_of_top = UserFactory.create()

        update_leaderboard()

        leaderboard = cached_users.get_leaderboard(3, user_id=user_out_of_top.id)

        assert len(leaderboard) is 4, len(leaderboard)
        assert leaderboard[-1]['name'] == user_out_of_top.name

    @with_context
    def test_get_leaderboard_returns_fields(self):
        """Test CACHE USERS get_leaderboard returns user fields"""
        user = UserFactory.create()
        TaskRunFactory.create(user=user)
        fields = User.public_attributes()

        update_leaderboard()
        leaderboard = cached_users.get_leaderboard(1)

        for field in fields:
            assert field in list(leaderboard[0].keys()), field
        assert len(list(leaderboard[0].keys())) == len(fields)

    @with_context
    def test_get_total_users_returns_0_if_no_users(self):
        total_users = cached_users.get_total_users()

        assert total_users == 0, total_users

    @with_context
    def test_get_total_users_returns_number_of_users(self):
        expected_number_of_users = 3
        UserFactory.create_batch(expected_number_of_users)

        total_users = cached_users.get_total_users()

        assert total_users == expected_number_of_users, total_users

    @with_context
    def test_get_users_page_only_returns_users_with_contributions(self):
        users = UserFactory.create_batch(2)
        TaskRunFactory.create(user=users[0])

        users_with_contrib = cached_users.get_users_page(1)

        assert len(users_with_contrib) == 1, users_with_contrib

    @with_context
    def test_get_users_page_supports_pagination(self):
        users = UserFactory.create_batch(3)
        for user in users:
            TaskRunFactory.create(user=user)

        paginated_users = cached_users.get_users_page(page=2, per_page=1)

        assert len(paginated_users) == 1, paginated_users
        assert paginated_users[0]['name'] == users[1].name

    @with_context
    def test_get_users_page_returns_fields(self):
        user = UserFactory.create()
        TaskRunFactory.create(user=user)
        fields = User.public_attributes()

        users = cached_users.get_users_page(1)

        for field in fields:
            assert field in list(users[0].keys()), field
        assert len(list(users[0].keys())) == len(fields)
