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
from mock import patch
from nose.tools import assert_raises
from requests import Response
from pybossa.syncer import NotEnabled
from pybossa.syncer.project_syncer import ProjectSyncer
from default import Test, with_context
from factories import ProjectFactory, UserFactory


def create_response(ok=True, status_code=200, content=None):
    res = Response()
    res._ok = ok
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

    target_url = 'http://test.com'
    target_id = 'some_target_id'
    target_key = 'super-secret-key'

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.get_target', return_value=None)
    @patch('pybossa.syncer.category_syncer.CategorySyncer.get_target', return_value={'id': 1})
    @patch('pybossa.syncer.project_syncer.ProjectSyncer._create')
    @patch('pybossa.syncer.requests')
    def test_sync_create_new(self, fake_requests, mock_create, mock_cat, mock_get):
        project_syncer = ProjectSyncer(self.target_url, self.target_key)
        user = UserFactory.create(admin=True, email_addr=u'user@test.com')
        project_syncer.syncer = user

        fake_requests.get.return_value = create_response(True, 200, json.dumps({'info': {'x':1}}))
        project = ProjectFactory.create()
        project_syncer.sync(project)
        project_syncer.get_target.assert_called_once()
        project_syncer._create.assert_called_once()

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.get_target')
    @patch('pybossa.syncer.category_syncer.CategorySyncer.get_target', return_value={'id': 1})
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.cache_target')
    @patch('pybossa.syncer.project_syncer.ProjectSyncer._sync')
    @patch('pybossa.syncer.requests')
    def test_sync_update_existing(self, fake_requests, mock_update, mock_cache, mock_cat, mock_get):
        project_syncer = ProjectSyncer(self.target_url, self.target_key)
        user = UserFactory.create(admin=True, email_addr=u'user@test.com')
        project_syncer.syncer = user

        mock_get.return_value = create_target()
        project = ProjectFactory.create()
        project_syncer.sync(project)
        project_syncer.get_target.assert_called_once()
        project_syncer.cache_target.assert_called_once()
        project_syncer._sync.assert_called_once()
        mock_cat.assert_called_once()

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.get_target')
    @patch('pybossa.syncer.category_syncer.CategorySyncer.get_target', return_value={'id': 1})
    @patch('pybossa.syncer.project_syncer.ProjectSyncer._sync')
    @patch('pybossa.syncer.requests')
    def test_sync_update_not_enabled(self, fake_requests, mock_update, mock_cat, mock_get):
        project_syncer = ProjectSyncer(self.target_url, self.target_key)
        user = UserFactory.create(admin=True, email_addr=u'user@test.com')
        project_syncer.syncer = user

        target = create_target()
        target['info']['sync']['enabled'] = False
        mock_get.return_value = target
        project = ProjectFactory.create()
        assert_raises(NotEnabled, project_syncer.sync, project)

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer._sync')
    @patch('pybossa.syncer.requests')
    def test_undo_sync_with_cache(self, fake_requests, eock_update):
        user = UserFactory.create(admin=True, email_addr=u'user@test.com')
        project_syncer = ProjectSyncer(self.target_url, self.target_key)

        project = ProjectFactory.build(short_name=self.target_id)
        project_syncer.cache_target(create_target(), self.target_id)
        project_syncer.undo_sync(project)
        project_syncer._sync.assert_called_once()

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer._sync')
    @patch('pybossa.syncer.requests')
    def test_undo_sync_without_cache(self, fake_requests, mock_update):
        user = UserFactory.create(admin=True, email_addr=u'user@test.com')
        project_syncer = ProjectSyncer(self.target_url, self.target_key)

        project = ProjectFactory.build(short_name=self.target_id)
        project_syncer.undo_sync(project)
        assert_raises(AssertionError, project_syncer._sync.assert_called)

    @with_context
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.get_target')
    @patch('pybossa.syncer.project_syncer.ProjectSyncer.get_user_email')
    @patch('pybossa.syncer.requests')
    def test_get_target_owners(self, fake_requests, mock_get_user_email, mock_get):
        user = UserFactory.create(admin=True, email_addr=u'user@test.com')
        project_syncer = ProjectSyncer(self.target_url, self.target_key)

        mock_get.return_value = create_target()
        project = ProjectFactory.build(short_name=self.target_id)
        project_syncer.get_target_owners(project)
        project_syncer.get_user_email.assert_called()

    @with_context
    @patch('pybossa.syncer.project_syncer.requests')
    @patch('pybossa.syncer.requests')
    def test_get_user_email(self, fake_requests, mock_requests):
        user = UserFactory.create(admin=True, email_addr=u'user@test.com')
        project_syncer = ProjectSyncer(self.target_url, self.target_key)
        content = json.dumps(user.dictize())
        mock_requests.get.return_value = create_response(content=content)
        project_syncer.get_user_email(user.id) == 'user@test.com'
