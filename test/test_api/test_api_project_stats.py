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
from default import with_context
from test_api import TestAPI
from factories import ProjectFactory, TaskFactory, TaskRunFactory
from pybossa.repositories import ProjectStatsRepository
import pybossa.cache.project_stats as stats

class TestProjectStatsAPI(TestAPI):

    @with_context
    def test_query_projectstats(self):
        """Test API query for project stats endpoint works"""
        project_stats = []
        projects = ProjectFactory.create_batch(3)
        for project in projects:
            for task in TaskFactory.create_batch(4, project=project, n_answers=3):
              TaskRunFactory.create(task=task)
            stats.update_stats(project.id)
            ps = stats.get_stats(project.id, full=True)
            project_stats.append(ps)

        extra_stat_types = ['hours_stats', 'dates_stats', 'users_stats']

        # As anon
        url = '/api/projectstats'
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert len(data) == 3, data

        # Limits
        res = self.app.get(url + "?limit=1")
        data = json.loads(res.data)
        assert len(data) == 1, data

        # Keyset pagination
        res = self.app.get(url + '?limit=1&last_id=' + str(projects[1].id))
        data = json.loads(res.data)
        assert len(data) == 1, len(data)
        assert data[0]['id'] == project.id

        # Errors
        res = self.app.get(url + "?something")
        err = json.loads(res.data)
        err_msg = "AttributeError exception should be raised"
        res.status_code == 415, err_msg
        assert res.status_code == 415, err_msg
        assert err['action'] == 'GET', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == 'AttributeError', err_msg

        # Desc filter
        url = "/api/projectstats?orderby=wrongattribute"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should be 415."
        assert data['status'] == 'failed', data
        assert data['status_code'] == 415, data
        assert 'has no attribute' in data['exception_msg'], data

        # Order by
        url = "/api/projectstats?orderby=id"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        ps_by_id = sorted(project_stats, key=lambda x: x.id, reverse=False)
        for i in range(len(project_stats)):
            assert ps_by_id[i].id == data[i]['id']

        # Desc filter
        url = "/api/projectstats?orderby=id&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        ps_by_id = sorted(project_stats, key=lambda x: x.id, reverse=True)
        for i in range(len(project_stats)):
            assert ps_by_id[i].id == data[i]['id']

        # Without full filter
        url = "/api/projectstats"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should not return the full stats."
        extra = [row['info'].get(_type) for _type in extra_stat_types
                 for row in data if row['info'].get(_type)]
        assert not extra

        # With full filter
        url = "/api/projectstats?full=1"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should return full stats."
        for i, row in enumerate(data):
            for _type in extra_stat_types:
                assert row['info'][_type] == project_stats[i].info[_type]
