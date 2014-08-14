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

from default import Test
from pybossa.cache import users as cached_users

from factories import AppFactory, TaskFactory, TaskRunFactory, UserFactory
from factories import reset_all_pk_sequences


class TestUsersCache(Test):


    def test_get_user_summary_nousers(self):
        """Test CACHE USERS get_user_summary returns None if no user exists with
        the name requested"""
        user = cached_users.get_user_summary('nouser')

        assert user is None, user


    def test_get_user_summary_user_exists(self):
        """Test CACHE USERS get_user_summary returns a dict with the user data
        if the user exists"""
        UserFactory.create(name='zidane')
        UserFactory.create(name='figo')

        zizou = cached_users.get_user_summary('zidane')

        assert type(zizou) is dict, type(zizou)
        assert zizou != None, zizou

    def test_get_user_summary_returns_fields(self):
        """Test CACHE USERS get_user_summary all the fields in the dict"""
        UserFactory.create(name='user')
        fields = ('id', 'name', 'fullname', 'created', 'api_key',
                  'twitter_user_id', 'google_user_id', 'facebook_user_id',
                  'info', 'email_addr', 'n_answers', 'rank', 'score', 'total')
        user = cached_users.get_user_summary('user')

        for field in fields:
            assert field in user.keys(), field


    def test_rank_and_score(self):
        """Test CACHE USERS rank_and_score returns the correct rank and score"""
        i = 0
        app = AppFactory.create()
        tasks = TaskFactory.create_batch(4, app=app)
        users = UserFactory.create_batch(4)
        for user in users:
            i += 1
            taskruns = TaskRunFactory.create_batch(i, user=user, task=tasks[i-1])

        first_in_rank = cached_users.rank_and_score(users[3].id)
        last_in_rank = cached_users.rank_and_score(users[0].id)
        print first_in_rank
        assert first_in_rank['rank'] == 1, first_in_rank['rank']
        assert first_in_rank['score'] == 4, first_in_rank['score']
        assert last_in_rank['rank'] == 4, last_in_rank['rank']
        assert last_in_rank['score'] == 1, last_in_rank['score']



    def test_apps_contributed_no_contributions(self):
        """Test CACHE USERS apps_contributed returns empty list if the user has
        not contributed to any project"""
        user = UserFactory.create()

        apps_contributed = cached_users.apps_contributed(user.id)

        assert apps_contributed == [], apps_contributed


    def test_apps_contributed_contributions(self):
        """Test CACHE USERS apps_contributed returns a list of projects that has
        contributed to"""
        user = UserFactory.create()
        app_contributed = AppFactory.create()
        task = TaskFactory.create(app=app_contributed)
        TaskRunFactory.create(task=task, user=user)
        another_app = AppFactory.create()

        apps_contributed = cached_users.apps_contributed(user.id)

        assert len(apps_contributed) == 1
        assert apps_contributed[0]['short_name'] == app_contributed.short_name, apps_contributed


    def test_apps_contributed_returns_fields(self):
        """Test CACHE USERS apps_contributed returns the info of the projects with
        the required fields"""
        user = UserFactory.create()
        app_contributed = AppFactory.create()
        task = TaskFactory.create(app=app_contributed)
        TaskRunFactory.create(task=task, user=user)
        fields = ('name', 'short_name', 'info', 'n_task_runs')

        apps_contributed = cached_users.apps_contributed(user.id)

        for field in fields:
            assert field in apps_contributed[0].keys(), field


    def test_published_apps_no_projects(self):
        """Test CACHE USERS published_apps returns empty list if the user has
        not created any project"""
        user = UserFactory.create()

        apps_published = cached_users.published_apps(user.id)

        assert apps_published == [], apps_published


    def test_published_apps_returns_published(self):
        """Test CACHE USERS published_apps returns a list with the projects that
        are published by the user"""
        user = UserFactory.create()
        published_project = AppFactory.create(owner=user)
        TaskFactory.create(app=published_project)

        apps_published = cached_users.published_apps(user.id)

        assert len(apps_published) == 1, apps_published
        assert apps_published[0]['short_name'] == published_project.short_name, apps_published


    def test_published_apps_only_returns_published(self):
        """Test CACHE USERS published_apps does not return hidden, draft
        or another user's projects"""
        user = UserFactory.create()
        another_user_published_project = AppFactory.create()
        TaskFactory.create(app=another_user_published_project)
        draft_project = AppFactory.create(info={})
        hidden_project = AppFactory.create(owner=user, hidden=1)
        TaskFactory.create(app=hidden_project)

        apps_published = cached_users.published_apps(user.id)

        assert len(apps_published) == 0, apps_published


    def test_published_apps_returns_fields(self):
        """Test CACHE USERS published_apps returns the info of the projects with
        the required fields"""
        user = UserFactory.create()
        published_project = AppFactory.create(owner=user)
        task = TaskFactory.create(app=published_project)
        fields = ('id', 'name', 'short_name', 'owner_id', 'description', 'info')

        apps_published = cached_users.published_apps(user.id)

        for field in fields:
            assert field in apps_published[0].keys(), field


    def test_draft_apps_no_projects(self):
        """Test CACHE USERS draft_apps returns an empty list if the user has no
        draft projects"""
        user = UserFactory.create()
        published_project = AppFactory.create(owner=user)

        draft_projects = cached_users.draft_apps(user.id)

        assert len(draft_projects) == 0, draft_projects


    def test_draft_apps_return_drafts(self):
        """Test CACHE USERS draft_apps returns draft belonging to the user"""
        user = UserFactory.create()
        draft_project = AppFactory.create(owner=user, info={})

        draft_projects = cached_users.draft_apps(user.id)

        assert len(draft_projects) == 1, draft_projects
        assert draft_projects[0]['short_name'] == draft_project.short_name, draft_projects


    def test_draft_apps_only_returns_drafts(self):
        """Test CACHE USERS draft_apps does not return any apps that are not draft
        (published) or drafts that belong to another user"""
        user = UserFactory.create()
        published_project = AppFactory.create(owner=user)
        TaskFactory.create(app=published_project)
        other_users_draft_project = AppFactory.create(info={})

        draft_projects = cached_users.draft_apps(user.id)

        assert len(draft_projects) == 0, draft_projects


    def test_draft_apps_hidden(self):
        """Test CACHE USERS draft_apps returns a project that belongs to the
        user and is a draft, even it's marked as hidden"""
        user = UserFactory.create()
        hidden_draft_project = AppFactory.create(owner=user, hidden=1, info={})

        draft_projects = cached_users.draft_apps(user.id)

        assert len(draft_projects) == 1, draft_projects


    def test_draft_apps_returns_fields(self):
        """Test CACHE USERS draft_apps returns the info of the projects with
        the required fields"""
        user = UserFactory.create()
        draft_project = AppFactory.create(owner=user, info={})
        fields = ('id', 'name', 'short_name', 'owner_id', 'description', 'info')

        draft_project = cached_users.draft_apps(user.id)

        for field in fields:
            assert field in draft_project[0].keys(), field


    def test_hidden_apps_no_projects(self):
        """Test CACHE USERS hidden_apps returns empty list if the user has
        not created any hidden project"""
        user = UserFactory.create()

        hidden_projects = cached_users.hidden_apps(user.id)

        assert hidden_projects == [], hidden_projects


    def test_hidden_apps_returns_hidden(self):
        """Test CACHE USERS hidden_apps returns a list with the user projects that
        are no drafts but are hidden"""
        user = UserFactory.create()
        hidden_project = AppFactory.create(owner=user, hidden=1)
        TaskFactory.create(app=hidden_project)

        hidden_projects = cached_users.hidden_apps(user.id)

        assert len(hidden_projects) == 1, hidden_projects
        assert hidden_projects[0]['short_name'] == hidden_project.short_name, hidden_projects


    def test_hidden_apps_only_returns_hidden(self):
        """Test CACHE USERS hidden_apps does not return draft (even hidden)
        or another user's hidden projects"""
        user = UserFactory.create()
        another_user_hidden_project = AppFactory.create(hidden=1)
        TaskFactory.create(app=another_user_hidden_project)
        hidden_draft_project = AppFactory.create(owner=user, hidden=1, info={})

        hidden_projects = cached_users.hidden_apps(user.id)

        assert len(hidden_projects) == 0, hidden_projects


    def test_hidden_apps_returns_fields(self):
        """Test CACHE USERS hidden_apps returns the info of the projects with
        the required fields"""
        user = UserFactory.create()
        hidden_project = AppFactory.create(owner=user, hidden=1)
        TaskFactory.create(app=hidden_project)
        fields = ('id', 'name', 'short_name', 'owner_id', 'description', 'info')

        hidden_projects = cached_users.hidden_apps(user.id)

        for field in fields:
            assert field in hidden_projects[0].keys(), field
