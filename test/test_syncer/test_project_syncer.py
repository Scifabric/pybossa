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
from mock import patch, Mock
from nose.tools import assert_raises
from requests import Response
from pybossa.syncer import NotEnabled
from pybossa.syncer.project_syncer import ProjectSyncer
from default import Test, with_context
from factories import ProjectFactory, UserFactory


def create_response(status_code=200, content=None):
    res = Response()
    res.status_code = status_code
    res._content = content
    return res


def create_target():
    return {
        'info': {'task_presenter': 'test', 'sync': {'enabled': True}},
        'category_id': 1,
        'description': 'test',
        'short_name': 'test_sync',
        'created': '2017-09-05T20:27:16.553977',
        'long_description': 'test',
        'owner_id': 1,
        'owners_ids': [1, 2, 3],
        'id': 1}


class TestProjectSyncer(Test):

    TARGET_URL = 'http://test.com'
    TARGET_ID = 'some_target_id'
    TARGET_KEY = 'super-secret-key'

    def setUp(self):
        super(TestProjectSyncer, self).setUp()
        self.project_syncer = ProjectSyncer()

    def test_is_sync_enabled(self):
        project_enabled = ProjectFactory.build(
            info={'sync': {'enabled': True}})
        project_enabled = project_enabled.__dict__
        project_disabled = ProjectFactory.build(
            info={'sync': {'enabled': False}})
        project_disabled = project_disabled.__dict__

        assert self.project_syncer.is_sync_enabled(project_enabled) == True
        assert self.project_syncer.is_sync_enabled(project_disabled) == False

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.get', return_value=None)
    @patch('pybossa.syncer.project_syncer.ProjectSyncer._create_new_project')
    def test_sync_create_new(self, mock_create, mock_get):
        project = ProjectFactory.create()
        admin = UserFactory(admin=True, email_addr=u'admin@test.com')
        self.project_syncer.sync(project, self.TARGET_URL, self.TARGET_KEY, admin)
        self.project_syncer.get.assert_called_once()
        self.project_syncer._create_new_project.assert_called_once()

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.get')
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.cache_target')
    @patch('pybossa.syncer.project_syncer.ProjectSyncer._sync')
    def test_sync_update_existing(self, mock_update, mock_cache, mock_get):
        mock_get.return_value = create_target()
        project = ProjectFactory.create()
        admin = UserFactory(admin=True, email_addr=u'admin@test.com')
        self.project_syncer.sync(project, self.TARGET_URL, self.TARGET_KEY, admin)
        self.project_syncer.get.assert_called_once()
        self.project_syncer.cache_target.assert_called_once()
        self.project_syncer._sync.assert_called_once()

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.get')
    @patch('pybossa.syncer.project_syncer.ProjectSyncer._sync')
    def test_sync_update_not_enabled(self, mock_update, mock_get):
        target = create_target()
        target['info']['sync']['enabled'] = False
        mock_get.return_value = target
        project = ProjectFactory.create()
        admin = UserFactory(admin=True, email_addr=u'admin@test.com')
        assert_raises(
            NotEnabled, self.project_syncer.sync, project,
            self.TARGET_URL, self.TARGET_KEY, admin)

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer._sync')
    def test_undo_sync_with_cache(self, mock_update):
        project = ProjectFactory.build(short_name=self.TARGET_ID)
        self.project_syncer.cache_target(create_target(), self.TARGET_URL, self.TARGET_ID)
        self.project_syncer.undo_sync(project, self.TARGET_URL, self.TARGET_KEY)
        self.project_syncer._sync.assert_called_once()

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer._sync')
    def test_undo_sync_without_cache(self, mock_update):
        project = ProjectFactory.build(short_name=self.TARGET_ID)
        self.project_syncer.undo_sync(project, self.TARGET_URL, self.TARGET_KEY)
        assert_raises(
            AssertionError, self.project_syncer._sync.assert_called)

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.get')
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.get_user_email')
    def test_get_target_owners(self, mock_get_user_email, mock_get):
        mock_get.return_value = create_target()
        project = ProjectFactory.build(short_name=self.TARGET_ID)
        self.project_syncer.get_target_owners(project, self.TARGET_URL, self.TARGET_KEY)
        self.project_syncer.get_user_email.assert_called()

    @with_context
    @patch('pybossa.syncer.project_syncer.requests')
    def test_get_user_email(self, mock_requests):
        email_addr = u'me@test.com'
        user = UserFactory.create(email_addr=email_addr)
        content = json.dumps(user.dictize())
        mock_requests.get.return_value = create_response(content=content)
        self.project_syncer.get_user_email(user.id, self.TARGET_URL, self.TARGET_KEY) == email_addr
