# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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
import json
from default import db, Test, with_context
from factories import AppFactory, AuditlogFactory, UserFactory

from pybossa.repositories import ProjectRepository
from pybossa.repositories import AuditlogRepository

project_repo = ProjectRepository(db)
auditlog_repo = AuditlogRepository(db)

class TestAuditlog(Test):

    @with_context
    def test_app_update_attributes(self):
        """Test Auditlog API project update attributes works."""
        app = AppFactory.create()

        data = {'name': 'New Name',
                'short_name': 'new_short_name',
                'description': 'new_description',
                'long_description': 'new_long_description',
                'allow_anonymous_contributors': 'false',
                }
        attributes = data.keys()
        url = '/api/app/%s?api_key=%s' % (app.id, app.owner.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(app_id=app.id)

        assert len(logs) == 5, logs
        for log in logs:
            assert log.user_id == app.owner_id, log.user_id
            assert log.user_name == app.owner.name, log.user_name
            assert log.app_short_name == app.short_name, log.app_short_name
            assert log.caller == 'api', log.caller
            assert log.attribute in attributes, log.attribute
            msg = "%s != %s" % (data[log.attribute], log.new_value)
            assert data[log.attribute] == log.new_value, msg

    @with_context
    def test_app_update_attributes_admin(self):
        """Test Auditlog API project update attributes works for admins."""
        app = AppFactory.create()
        admin = UserFactory.create(admin=True)

        data = {'name': 'New Name',
                'short_name': 'new_short_name',
                'description': 'new_description',
                'long_description': 'new_long_description',
                'allow_anonymous_contributors': 'false',
                }
        attributes = data.keys()
        url = '/api/app/%s?api_key=%s' % (app.id, admin.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(app_id=app.id)

        assert len(logs) == 5, logs
        for log in logs:
            assert log.user_id == admin.id, log.user_id
            assert log.user_name == admin.name, log.user_name
            assert log.app_short_name == app.short_name, log.app_short_name
            assert log.caller == 'api', log.caller
            assert log.attribute in attributes, log.attribute
            msg = "%s != %s" % (data[log.attribute], log.new_value)
            assert data[log.attribute] == log.new_value, msg

    @with_context
    def test_app_update_attributes_non_owner(self):
        """Test Auditlog API project update attributes works for non owners."""
        app = AppFactory.create()
        user = UserFactory.create()

        data = {'name': 'New Name',
                'short_name': 'new_short_name',
                'description': 'new_description',
                'long_description': 'new_long_description',
                'allow_anonymous_contributors': 'false',
                }
        url = '/api/app/%s?api_key=%s' % (app.id, user.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(app_id=app.id)

        assert len(logs) == 0, logs

    def test_app_update_task_presenter(self):
        """Test Auditlog API project update info task_presenter works."""
        app = AppFactory.create()

        owner_id = app.owner.id
        owner_name = app.owner.name
        data = {'info': {'task_presenter': 'new'}}
        attributes = data.keys()
        url = '/api/app/%s?api_key=%s' % (app.id, app.owner.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(app_id=app.id)

        assert len(logs) == 1, logs
        for log in logs:
            assert log.user_id == owner_id, log.user_id
            assert log.user_name == owner_name, log.user_name
            assert log.app_short_name == app.short_name, log.app_short_name
            assert log.caller == 'api', log.caller
            assert log.attribute in attributes, log.attribute
            msg = "%s != %s" % (data[log.attribute], log.new_value)
            assert data[log.attribute]['task_presenter'] == json.loads(log.new_value)['task_presenter'], msg

    def test_app_update_scheduler(self):
        """Test Auditlog API project update info scheduler works."""
        app = AppFactory.create()

        owner_id = app.owner.id
        owner_name = app.owner.name
        data = {'info': {'sched': 'random'}}
        attributes = data.keys()
        url = '/api/app/%s?api_key=%s' % (app.id, app.owner.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(app_id=app.id)

        assert len(logs) == 1, logs
        for log in logs:
            assert log.user_id == owner_id, log.user_id
            assert log.user_name == owner_name, log.user_name
            assert log.app_short_name == app.short_name, log.app_short_name
            assert log.caller == 'api', log.caller
            assert log.attribute in attributes, log.attribute
            msg = "%s != %s" % (data[log.attribute], log.new_value)
            assert data[log.attribute]['sched'] == json.loads(log.new_value)['sched'], msg

    def test_app_update_two_info_objects(self):
        """Test Auditlog API project update two info objects works."""
        app = AppFactory.create()

        owner_id = app.owner.id
        owner_name = app.owner.name
        data = {'info': {'sched': 'random', 'task_presenter': 'new'}}
        attributes = data.keys()
        url = '/api/app/%s?api_key=%s' % (app.id, app.owner.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(app_id=app.id)

        assert len(logs) == 1, logs
        for log in logs:
            assert log.user_id == owner_id, log.user_id
            assert log.user_name == owner_name, log.user_name
            assert log.app_short_name == app.short_name, log.app_short_name
            assert log.caller == 'api', log.caller
            assert log.attribute in attributes, log.attribute
            msg = "%s != %s" % (data[log.attribute], log.new_value)
            assert data[log.attribute]['sched'] == json.loads(log.new_value)['sched'], msg
            assert data[log.attribute]['task_presenter'] == json.loads(log.new_value)['task_presenter'], msg
