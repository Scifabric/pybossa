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
# Cache global variables for timeouts

from default import Test, db, with_context
from factories import ProjectFactory, UserFactory, TaskFactory
from pybossa.repositories import ProjectStatsRepository
import pybossa.cache.project_stats as stats


class TestProjectStatsRepository(Test):

    def setUp(self):
        super(TestProjectStatsRepository, self).setUp()
        self.projectstats_repo = ProjectStatsRepository(db)

    def prepare_stats(self, n=1):
      project = ProjectFactory.create()
      TaskFactory.create_batch(n, project=project)
      stats.update_stats(project.id)
      return stats.get_stats(project.id, full=True)

    @with_context
    def test_get_return_none_if_no_stats(self):
        """Test get method returns None if no stats with the specified id"""
        ps = self.projectstats_repo.get(2)
        assert ps is None, ps

    @with_context
    def test_get_returns_stats(self):
        """Test get method returns project stats if they exist"""
        ps = self.prepare_stats()
        retrieved_ps = self.projectstats_repo.get(ps.id)
        assert ps == retrieved_ps, retrieved_ps

    @with_context
    def test_filter_by_no_matches(self):
        """Test filter_by returns an empty list if no stats match the query"""
        ps = self.prepare_stats()
        retrieved_ps = self.projectstats_repo.filter_by(n_tasks=100)
        assert isinstance(retrieved_ps, list)
        assert len(retrieved_ps) == 0, retrieved_ps


    @with_context
    def test_filter_by_one_condition(self):
        """Test filter_by returns a list of logs that meet the filtering
        condition"""
        ps1 = self.prepare_stats(3)
        ps2 = self.prepare_stats(3)
        should_be_missing = self.prepare_stats(5)
        retrieved_ps = self.projectstats_repo.filter_by(n_tasks=3)

        assert len(retrieved_ps) == 2, retrieved_ps
        assert should_be_missing not in retrieved_ps, retrieved_ps


    @with_context
    def test_filter_by_multiple_conditions(self):
        """Test filter_by supports multiple-condition queries"""
        ps1 = self.prepare_stats(3)
        ps2 = self.prepare_stats(5)
        retrieved_ps = self.projectstats_repo.filter_by(project_id=ps1.project_id,
                                                        n_tasks=3)
        assert len(retrieved_ps) == 1, retrieved_ps
        assert ps1 in retrieved_ps, retrieved_ps
