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
from default import db, with_context
from nose.tools import assert_equal
from test_api import TestAPI

from factories import TaskFactory, UserFactory

from pybossa.repositories import TaskRepository

task_repo = TaskRepository(db)

class TestFavoritesAPI(TestAPI):

    url = 'api/favorites'

    @with_context
    def test_query_favorites_anon(self):
        """Test API Favorites works for anon."""
        user = UserFactory.create()
        task = TaskFactory.create(fav_user_ids=[user.id])
        res = self.app.get(self.url)
        data = json.loads(res.data)
        assert res.status_code == 401
        assert data['status_code'] == 401
