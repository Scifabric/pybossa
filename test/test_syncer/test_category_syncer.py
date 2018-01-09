# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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
from pybossa.syncer.category_syncer import CategorySyncer
from default import Test, db, with_context
from factories import ProjectFactory, UserFactory, CategoryFactory


class TestCategorySyncer(Test):

    target_url = 'http://test.com'
    target_key = 'super-secret-key'

    @with_context
    @patch('pybossa.syncer.project_syncer.CategorySyncer.get_target', return_value=None)
    @patch('pybossa.syncer.project_syncer.CategorySyncer._create')
    @patch('pybossa.syncer.project_syncer.CategorySyncer._build_payload')
    @patch('pybossa.syncer.requests')
    def test_sync(self, fake_requests, mocl_build, mock_create, mock_get):
        category_syncer = CategorySyncer(self.target_url, self.target_key)
        category = CategoryFactory.create()
        category_syncer.sync(category)

        category_syncer.get_target.assert_called_once()
        category_syncer._create.assert_called_once()
