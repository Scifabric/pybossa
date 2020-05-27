# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2019 Scifabric LTD.
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
from test_api import TestAPI
from factories import ProjectFactory, AuditlogFactory, UserFactory

from pybossa.repositories import ProjectRepository
from pybossa.repositories import AuditlogRepository

project_repo = ProjectRepository(db)
auditlog_repo = AuditlogRepository(db)


class TestAuditlogAPI(TestAPI):

    def create_auditlogs(self):
        project = ProjectFactory.create(
            info={
                'task_presenter': 'version1',
                'task_guidelines': 'version1',
                'data_classification': dict(input_data="L4 - public", output_data="L4 - public")
            })

        AuditlogFactory.create(project_id=project.id,
            project_short_name=project.short_name,
            user_id=project.owner.id,
            user_name=project.owner.name,
            attribute='task_presenter',
            old_value="old_task_presenter1",
            new_value="new_task_presenter2",
            created='2019-01-11T15:24:42.263980')

        AuditlogFactory.create_batch(size=3, project_id=project.id,
            project_short_name=project.short_name,
            user_id=project.owner.id,
            user_name=project.owner.name,
            attribute='task_guidelines',
            old_value="old_task_guidelines1",
            new_value="new_task_guidelines2",
            created='2019-01-11T15:24:42.263980')

        AuditlogFactory.create_batch(size=3, project_id=project.id,
            project_short_name=project.short_name,
            user_id=project.owner.id,
            user_name=project.owner.name,
            attribute='task_guidelines',
            old_value="old_task_guidelines1",
            new_value="new_task_guidelines2",
            created='2020-01-11T15:24:42.263980')

    @with_context
    def test_auditlog_created_to(self):
        """Test API query for auditlog with  this params created_to, attribute, project_id  works"""
        self.create_auditlogs()
        user = UserFactory.create(admin=True)

        res = self.app.get('/api/auditlog?project_id=1&created_to=2020-01-11T15:24:42.263980&attribute=task_guidelines&all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 6, data
        assert data[0]['project_id'] == 1, data
        assert data[0]['attribute'] == 'task_guidelines', data

        res = self.app.get('/api/auditlog?project_id=1&created_to=2020-01-11T15:24:42.263980&attribute=task_presenter&all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, data
        assert data[0]['project_id'] == 1, data
        assert data[0]['attribute'] == 'task_presenter', data

        res = self.app.get('/api/auditlog?project_id=1&created_to=2019-01-11T15:24:42.263980&attribute=task_presenter&all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, data


    @with_context
    def test_auditlog_created_from(self):
        """Test API query for auditlog with  this params created_from, attribute, project_id  works"""
        self.create_auditlogs()
        user = UserFactory.create(admin=True)

        res = self.app.get('/api/auditlog?project_id=1&created_from=2020-01-10T15:24:42.263980&attribute=task_guidelines&all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 3, data
        assert data[0]['project_id'] == 1, data
        assert data[0]['attribute'] == 'task_guidelines', data

        res = self.app.get('/api/auditlog?project_id=1&created_from=2019-01-10T15:24:42.263980&attribute=task_presenter&all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, data
        assert data[0]['project_id'] == 1, data
        assert data[0]['attribute'] == 'task_presenter', data

        res = self.app.get('/api/auditlog?project_id=1&created_from=2019-01-10T15:24:42.263980&attribute=task_guidelines&all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 6, len(data)

    @with_context
    def test_auditlog_all(self):
        """Test API query for auditlog works"""
        self.create_auditlogs()
        user = UserFactory.create(admin=True)
        res = self.app.get('/api/auditlog?project_id=1&all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 7, data
        assert data[0]['project_id'] == 1, data

    def test_post_not_allowed(self):
        url = '/api/auditlog'
        res = self.app.post(url)
        assert res.status_code == 405, res.status

    def test_put_not_allowed(self):
        url = '/api/auditlog/1'
        res = self.app.put(url)
        assert res.status_code == 405, res.status

    def test_delete_not_allowed(self):
        url = '/api/auditlog/1'
        res = self.app.delete(url)
        assert res.status_code == 405, res.status


