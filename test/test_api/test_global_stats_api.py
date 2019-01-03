# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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
from default import with_context
from test_api import TestAPI
from factories import ProjectFactory



class TestGlobalStatsAPI(TestAPI):

    @with_context
    def test_global_stats(self):
        """Test Global Stats works."""
        ProjectFactory()
        res = self.app.get('api/globalstats')
        stats = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        keys = ['n_projects', 'n_pending_tasks',
                'n_tasks',
                'n_users', 'n_task_runs', 'n_results', 'categories']
        for k in keys:
            err_msg = "%s should be in stats JSON object" % k
            assert k in list(stats.keys()), err_msg

    @with_context
    def test_post_global_stats(self):
        """Test Global Stats Post works."""
        res = self.app.post('api/globalstats')
        assert res.status_code == 405, res.status_code
