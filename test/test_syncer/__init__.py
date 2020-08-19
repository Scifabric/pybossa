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
from default import Test, with_context
from factories import ProjectFactory
from nose.tools import assert_raises


class TestSyncer(Test):

    target = {'short_name': 'some_project', 'id': 1}
    target_url = 'http://test.com'
    target_key = 'super-secret-key'
    target_id = 'some_target_id'

    def setUp(self):
        from pybossa.syncer import Syncer
        super(TestSyncer, self).setUp()
        self.syncer = Syncer(self.target_url, self.target_key)

    @with_context
    def test_cache_target(self):
        self.syncer.cache_target(self.target, self.target_id)
        cache = self.syncer.get_target_cache(self.target_id)
        assert cache == self.target

        self.syncer.delete_target_cache(self.target_id)
        cache = self.syncer.get_target_cache(self.target_id)
        assert cache == None

    def test_is_sync_enabled(self):
        project_enabled = ProjectFactory.build(info={'sync': {'enabled': True}})
        project_enabled = project_enabled.__dict__
        project_disabled = ProjectFactory.build(info={'sync': {'enabled': False}})
        project_disabled = project_disabled.__dict__

        assert self.syncer.is_sync_enabled(project_enabled) == True
        assert self.syncer.is_sync_enabled(project_disabled) == False

    @patch('pybossa.syncer.requests.get')
    def test_get_target(self, http_get):
        res = http_get.return_value
        res.ok = True
        res.content = json.dumps([])
        assert self.syncer.get_target() is None

    def test_not_implemented(self):
        assert_raises(NotImplementedError, self.syncer.sync, 'a')
        assert_raises(NotImplementedError, self.syncer.undo_sync, 'a')
