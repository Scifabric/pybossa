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

import json
from bs4 import BeautifulSoup
from helper import web as web_helper
from default import flask_app, with_context
from mock import patch
from factories import ProjectFactory, UserFactory, TaskFactory, TaskRunFactory
from pybossa.cache.project_stats import update_stats


class TestPrivacyWebPublic(web_helper.Helper):

    # Tests
    @with_context
    def test_00_footer(self):
        '''Test PRIVACY footer privacy is respected'''
        url = '/'
        # As Anonymou user
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Footer links should be shown to anonymous users'
        assert dom.find('footer') is not None, err_msg
        # As Authenticated user but NOT ADMIN
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Footer links should be shown to authenticated users'
        assert dom.find('footer') is not None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Footer links should be shown to admin users'
        assert dom.find('footer') is not None, err_msg
        self.signout()

    @with_context
    def test_01_front_page(self):
        '''Test PRIVACY footer privacy is respected'''
        url = '/'
        # As Anonymou user
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        # TODO: old requirement, remove in future versions?
        # err_msg = 'Top users should be shown to anonymous users'
        # assert dom.find(id='top_users') is not None, err_msg
        # As Authenticated user but NOT ADMIN
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        # TODO: old requirement, remove in future versions?
        # err_msg = 'Top users should be shown to authenticated users'
        # assert dom.find(id='top_users') is not None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        # TODO: Old requirement, remove in future versions?
        # err_msg = 'Top users should be shown to admin'
        # assert dom.find(id='top_users') is not None, err_msg
        self.signout()

    @with_context
    def test_02_account_index(self):
        '''Test PRIVACY account privacy is respected'''
        # As Anonymou user
        url = '/account'
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Community page should be shown to anonymous users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        # As Authenticated user but NOT ADMIN
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Community page should be shown to authenticated users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Community page should be shown to admin users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout()

    @with_context
    def test_03_leaderboard(self):
        '''Test PRIVACY leaderboard privacy is respected'''
        # As Anonymou user
        url = '/leaderboard'
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Leaderboard page should be shown to anonymous users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        # As Authenticated user but NOT ADMIN
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Leaderboard page should be shown to authenticated users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Leaderboard page should be shown to admin users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout()

    @with_context
    def test_04_global_stats_index(self):
        '''Test PRIVACY global stats privacy is respected'''
        # As Anonymou user
        url = '/stats'
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Stats page should be shown to anonymous users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        # As Authenticated user but NOT ADMIN
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Stats page should be shown to authenticated users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Stats page should be shown to admin users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout()

    @with_context
    def test_05_app_stats_index(self):
        '''Test PRIVACY project stats privacy is respected'''
        # As Anonymou user
        url = '/project/%s/stats' % self.project_short_name
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Project Stats page should be shown to anonymous users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        # As Authenticated user but NOT ADMIN
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Project Stats page should be shown to authenticated users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Project Stats page should be shown to admin users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout()

    @with_context
    def test_06_user_public_profile(self):
        '''Test PRIVACY user public profile privacy is respected'''
        # As Anonymous user
        url = '/account/%s' % self.name
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Public User Profile page should be shown to anonymous users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        # As Authenticated user but NOT ADMIN
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Public User Profile page should be shown to authenticated users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Public User Profile page should be shown to admin users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout()

    @with_context
    def test_07_user_public_profile_json(self):
        '''Test PRIVACY user public profile privacy is respected for API access'''
        # As Anonymous user
        admin, user, owner = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        TaskRunFactory.create_batch(30, project=project)
        TaskRunFactory.create(user=owner)
        update_stats(project.id)
        url = '/account/%s' % owner.name
        # Use a full url to avoid redirection on API access.
        full_url = 'http://localhost%s/' % url
        res = self.app.get(full_url, content_type='application/json')
        data = json.loads(res.data)
        print(list(data.keys()))
        # this data should be public visible in user
        err_msg = 'name should be public'
        assert data['user']['name'] == owner.name, err_msg
        err_msg = 'fullname should be public'
        assert data['user']['fullname'] == owner.fullname, err_msg
        err_msg = 'rank should be public'
        assert 'rank' in data['user'], err_msg
        err_msg = 'score should be public'
        assert 'score' in data['user'], err_msg
        # this data should not be public in user
        err_msg = 'id should not be public'
        assert 'id' not in data['user'], err_msg
        err_msg = 'api_key should not be public'
        assert 'api_key' not in data['user'], err_msg
        err_msg = 'confirmation_email_sent should not be public'
        assert 'confirmation_email_sent' not in data['user'], err_msg
        err_msg = 'email_addr should not be public'
        assert 'email_addr' not in data['user'], err_msg
        err_msg = 'google_user_id should not be public'
        assert 'google_user_id' not in data['user'], err_msg
        err_msg = 'facebook_user_id should not be public'
        assert 'facebook_user_id' not in data['user'], err_msg
        err_msg = 'twitter_user_id should not be public'
        assert 'twitter_user_id' not in data['user'], err_msg
        err_msg = 'valid_email should not be public'
        assert 'valid_email' not in data['user'], err_msg
        # public projects data
        print(data)
        project = data['projects'][0]
        err_msg = 'info should be public'
        assert 'info' in project, err_msg
        err_msg = 'description should be public'
        assert 'description' in project, err_msg
        err_msg = 'short_name should be public'
        assert 'short_name' in project, err_msg
        err_msg = 'n_tasks should be public'
        assert 'n_tasks' in project, err_msg
        err_msg = 'n_volunteers should be public'
        assert 'n_volunteers' in project, err_msg
        err_msg = 'overall_progress should be public'
        assert 'overall_progress' in project, err_msg
        err_msg = 'name should be public'
        assert 'name' in project, err_msg
        # non public projects data
        # err_msg = 'id should not be public'
        # assert 'id' not in project, err_msg
        err_msg = 'secret_key should not be public'
        assert 'secret_key' not in project, err_msg
        err_msg = 'results should not be public'
        assert 'results' not in project['info'], err_msg
        err_msg = 'onesignal should not be public'
        assert 'onesignal' not in project['info'], err_msg

    @with_context
    def test_08_user_public_profile_json(self):
        '''Test PRIVACY user public profile privacy is respected for API access'''
        # As Anonymous user
        url = '/account/profile'
        # Use a full url to avoid redirection on API access.
        full_url = 'http://localhost%s/' % url
        res = self.app.get(full_url, content_type='application/json')
        data = json.loads(res.data)
        err_msg = 'no information should be shown here'
        assert 'user' not in data, err_msg
        assert 'projects' not in data, err_msg


class TestPrivacyWebPrivacy(web_helper.Helper):

    # Tests
    @patch.dict(flask_app.config, {'ENFORCE_PRIVACY': True})
    @with_context
    def test_00_footer(self):
        '''Test PRIVACY footer privacy is respected'''
        url = '/'
        # As Anonymou user
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Footer links should not be shown to anonymous users'
        assert dom.find(id='footer_links') is None, err_msg
        # As Authenticated user but NOT ADMIN
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Footer links should not be shown to authenticated users'
        assert dom.find(id='footer_links') is None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        self.signin(email=self.root_addr, password=self.root_password)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Footer links should not be shown to admin users'
        assert dom.find(id='footer_links') is None, err_msg
        self.signout()

    @patch.dict(flask_app.config, {'ENFORCE_PRIVACY': True})
    @with_context
    def test_01_front_page(self):
        '''Test PRIVACY front page top users privacy is respected'''
        url = '/'
        # As Anonymou user
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Top users should not be shown to anonymous users'
        assert dom.find(id='top_users') is None, err_msg
        # As Authenticated user but NOT ADMIN
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Top users should not be shown to authenticated users'
        assert dom.find(id='top_users') is None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        res = self.signin(email=self.root_addr, password=self.root_password)
        print(res.data)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        # TODO: old requirement, remove in future versions
        # err_msg = 'Top users should be shown to admin'
        # assert dom.find(id='top_users') is not None, err_msg
        self.signout()

    @patch.dict(flask_app.config, {'ENFORCE_PRIVACY': True})
    @with_context
    def test_02_account_index(self):
        '''Test PRIVACY account privacy is respected'''
        admin, user, owner = UserFactory.create_batch(3)
        # As Anonymou user
        url = '/account'
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Community page should not be shown to anonymous users'
        assert dom.find(id='enforce_privacy') is not None, err_msg
        # As Authenticated user but NOT ADMIN
        res = self.app.get(url + '?api_key=%s' % user.api_key,
                           follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Community page should not be shown to authenticated users'
        assert dom.find(id='enforce_privacy') is not None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        res = self.app.get(url + '?api_key=%s' % admin.api_key, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Community page should be shown to admin users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout()

    @patch.dict(flask_app.config, {'ENFORCE_PRIVACY': True})
    @with_context
    def test_03_leaderboard(self):
        '''Test PRIVACY leaderboard privacy is respected'''
        admin, user, owner = UserFactory.create_batch(3)
        # As Anonymou user
        url = '/leaderboard'
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Leaderboard page should not be shown to anonymous users'
        assert dom.find(id='enforce_privacy') is not None, err_msg
        # As Authenticated user but NOT ADMIN
        res = self.app.get(url + '?api_key=%s' % user.api_key, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Leaderboard page should not be shown to authenticated users'
        assert dom.find(id='enforce_privacy') is not None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        res = self.app.get(url + '?api_key=%s' % admin.api_key, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Leaderboard page should be shown to admin users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout()

    @patch.dict(flask_app.config, {'ENFORCE_PRIVACY': True})
    @with_context
    def test_04_global_stats_index(self):
        '''Test PRIVACY global stats privacy is respected'''
        admin, user, owner = UserFactory.create_batch(3)
        # As Anonymou user
        url = '/stats'
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Stats page should not be shown to anonymous users'
        assert dom.find(id='enforce_privacy') is not None, err_msg
        # As Authenticated user but NOT ADMIN
        self.signin()
        res = self.app.get(url + '?api_key=%s' % user.api_key, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Stats page should not be shown to authenticated users'
        assert dom.find(id='enforce_privacy') is not None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        res = self.app.get(url + '?api_key=%s' % admin.api_key, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Stats page should be shown to admin users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout()

    @patch.dict(flask_app.config, {'ENFORCE_PRIVACY': True})
    @with_context
    def test_05_app_stats_index(self):
        '''Test PRIVACY project stats privacy is respected'''
        # As Anonymou user
        admin, user, owner = UserFactory.create_batch(3)
        task = TaskFactory.create(n_answers=3)
        TaskRunFactory.create_batch(3, task=task)
        url = '/project/%s/stats' % task.project.short_name
        update_stats(task.project.id)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Project Stats page should not be shown to anonymous users'
        assert dom.find(id='enforce_privacy') is not None, res.data
        # As Authenticated user but NOT ADMIN
        res = self.app.get(url + '?api_key=%s' % user.api_key,
                           follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Project Stats page should not be shown to authenticated users'
        assert dom.find(id='enforce_privacy') is not None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        res = self.app.get(url + '?api_key=%s' % admin.api_key,
                           follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Project Stats page should be shown to admin users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout()

    @patch.dict(flask_app.config, {'ENFORCE_PRIVACY': True})
    @with_context
    def test_06_user_public_profile(self):
        '''Test PRIVACY user public profile privacy is respected'''
        admin, user, owner = UserFactory.create_batch(3)
        # As Anonymou user
        url = '/account/%s' % owner.name
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Public User Profile page should not be shown to anonymous users'
        assert dom.find(id='enforce_privacy') is not None, err_msg
        # As Authenticated user but NOT ADMIN
        res = self.app.get(url + '?api_key=%s' % user.api_key, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Public User Profile page should not be shown to authenticated users'
        assert dom.find(id='enforce_privacy') is not None, err_msg
        self.signout
        # As Authenticated user but ADMIN
        res = self.app.get(url + '?api_key=%s' % admin.api_key, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = 'Public User Profile page should be shown to admin users'
        assert dom.find(id='enforce_privacy') is None, err_msg
        self.signout()
