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
from factories import UserFactory, ProjectFactory, TaskFactory,\
    TaskRunFactory, PerformanceStatsFactory

class TestPerformanceStatsAPI(TestAPI):

    @with_context
    def test_query_projectstats_permissions(self):
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)

        url = '/api/performancestats'
        res = self.app.get('{}?api_key={}'.format(url, owner.api_key))
        assert json.loads(res.data) == []

        stats = PerformanceStatsFactory.create(user_id=user.id, project_id=project.id)

        res = self.app.get('{}?api_key={}'.format(url, admin.api_key))
        data = json.loads(res.data)
        assert not data

        res = self.app.get('{}?api_key={}&all=1'.format(url, admin.api_key))
        data = json.loads(res.data)
        assert len(data) == 1

        res = self.app.get('{}?api_key={}'.format(url, owner.api_key))
        data = json.loads(res.data)
        assert len(data) == 1

        res = self.app.get('{}?api_key={}'.format(url, user.api_key))
        data = json.loads(res.data)
        assert not data

        res = self.app.get('{}?api_key={}&all=1'.format(url, user.api_key))
        data = json.loads(res.data)
        assert not data

    @with_context
    def test_query_projectstats_filter_user(self):
        owner, user = UserFactory.create_batch(2)
        project = ProjectFactory.create(owner=owner)

        stats = PerformanceStatsFactory.create(
            user_id=user.id, project_id=project.id, info={'user': user.id})
        stats = PerformanceStatsFactory.create(
            user_id=owner.id, project_id=project.id, info={'user': owner.id})

        url = '/api/performancestats'
        res = self.app.get('{}?api_key={}&user_id={}'.format(url, owner.api_key, user.id))
        data = json.loads(res.data)
        assert len(data) == 1
        assert data[0]['info']['user'] == user.id

        res = self.app.get('{}?api_key={}&user_id={}'.format(url, owner.api_key, owner.id))
        data = json.loads(res.data)
        assert len(data) == 1
        assert data[0]['info']['user'] == owner.id

    @with_context
    def test_query_projectstats_filter_project(self):
        owner = UserFactory.create()
        project1, project2 = ProjectFactory.create_batch(2, owner=owner)

        stats = PerformanceStatsFactory.create(
            user_id=owner.id, project_id=project1.id, info={'project': project1.id})
        stats = PerformanceStatsFactory.create(
            user_id=owner.id, project_id=project2.id, info={'project': project2.id})

        url = '/api/performancestats'
        res = self.app.get('{}?api_key={}&project_id={}'.format(url, owner.api_key, project1.id))
        data = json.loads(res.data)
        assert len(data) == 1
        assert data[0]['info']['project'] == project1.id

        res = self.app.get('{}?api_key={}&project_id={}'.format(url, owner.api_key, project2.id))
        data = json.loads(res.data)
        assert len(data) == 1
        assert data[0]['info']['project'] == project2.id

    @with_context
    def test_query_projectstats_filter_type(self):
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)

        stats = PerformanceStatsFactory.create(
            stat_type='confusion_matrix',
            user_id=owner.id, project_id=project.id, info={'type': 'matrix'})
        stats = PerformanceStatsFactory.create(
            stat_type='accuracy',
            user_id=owner.id, project_id=project.id, info={'type': 'accuracy'})

        url = '/api/performancestats'
        res = self.app.get('{}?api_key={}&stat_type={}'.format(url, owner.api_key, 'confusion_matrix'))
        data = json.loads(res.data)
        assert len(data) == 1
        assert data[0]['info']['type'] == 'matrix'

        res = self.app.get('{}?api_key={}&stat_type={}'.format(url, owner.api_key, 'accuracy'))
        data = json.loads(res.data)
        assert len(data) == 1
        assert data[0]['info']['type'] == 'accuracy'

    @with_context
    def test_query_projectstats_filter_field(self):
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)

        stats = PerformanceStatsFactory.create(
            field='field_a',
            user_id=owner.id, project_id=project.id, info={'field': 'A'})
        stats = PerformanceStatsFactory.create(
            field='field_b',
            user_id=owner.id, project_id=project.id, info={'field': 'B'})

        url = '/api/performancestats'
        res = self.app.get('{}?api_key={}&field={}'.format(url, owner.api_key, 'field_a'))
        data = json.loads(res.data)
        assert len(data) == 1
        assert data[0]['info']['field'] == 'A'

        res = self.app.get('{}?api_key={}&field={}'.format(url, owner.api_key, 'field_b'))
        data = json.loads(res.data)
        assert len(data) == 1
        assert data[0]['info']['field'] == 'B'

    def test_post_not_allowed(self):
        url = '/api/performancestats'
        res = self.app.post(url)
        assert res.status_code == 405, res.status

    def test_put_not_allowed(self):
        url = '/api/performancestats/1'
        res = self.app.put(url)
        assert res.status_code == 405, res.status

    def test_delete_not_allowed(self):
        url = '/api/performancestats/1'
        res = self.app.delete(url)
        assert res.status_code == 405, res.status
