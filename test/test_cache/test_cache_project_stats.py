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

from default import Test, with_context
from pybossa.cache.project_stats import *
from factories import UserFactory, ProjectFactory, TaskFactory, \
    TaskRunFactory, AnonymousTaskRunFactory
from mock import patch


class TestProjectsStatsCache(Test):


    def test_stats_users(self):
        """Test CACHE PROJECT STATS user stats works."""
        pr = ProjectFactory.create()
        TaskRunFactory.create(project=pr)
        AnonymousTaskRunFactory.create(project=pr)
        users, anon_users, auth_users = stats_users(pr.id)
        assert len(users) == 2, len(users)
        assert len(anon_users) == 1, len(anon_users)
        assert len(auth_users) == 1, len(auth_users)

    def test_stats_users_with_period(self):
        """Test CACHE PROJECT STATS user stats with period works."""
        pr = ProjectFactory.create()
        TaskRunFactory.create(project=pr)
        AnonymousTaskRunFactory.create(project=pr)
        users, anon_users, auth_users = stats_users(pr.id, '1 week')
        assert len(users) == 2, len(users)
        assert len(anon_users) == 1, len(anon_users)
        assert len(auth_users) == 1, len(auth_users)
