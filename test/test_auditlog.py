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
from collections import namedtuple
from factories import AppFactory, AuditlogFactory, UserFactory
from helper import web

from pybossa.repositories import ProjectRepository
from pybossa.repositories import AuditlogRepository
from mock import patch

project_repo = ProjectRepository(db)
auditlog_repo = AuditlogRepository(db)


FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])

class TestAuditlogAPI(Test):

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
            assert log.attribute == 'task_presenter', log.attribute
            msg = "%s != %s" % (data['info']['task_presenter'], log.new_value)
            assert data['info']['task_presenter'] == json.loads(log.new_value), msg

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
            assert log.attribute == 'sched', log.attribute
            msg = "%s != %s" % (data['info']['sched'], log.new_value)
            assert data['info']['sched'] == json.loads(log.new_value), msg

    def test_app_update_two_info_objects(self):
        """Test Auditlog API project update two info objects works."""
        app = AppFactory.create()

        owner_id = app.owner.id
        owner_name = app.owner.name
        data = {'info': {'sched': 'random', 'task_presenter': 'new'}}
        attributes = data['info'].keys()
        url = '/api/app/%s?api_key=%s' % (app.id, app.owner.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(app_id=app.id)

        assert len(logs) == 2, logs
        for log in logs:
            assert log.user_id == owner_id, log.user_id
            assert log.user_name == owner_name, log.user_name
            assert log.app_short_name == app.short_name, log.app_short_name
            assert log.caller == 'api', log.caller
            assert log.attribute in attributes, log.attribute
            msg = "%s != %s" % (data['info'][log.attribute], log.new_value)
            assert data['info'][log.attribute] == json.loads(log.new_value), msg


class TestAuditlogWEB(web.Helper):

    data = {}
    editor = {}

    def setUp(self):
        super(TestAuditlogWEB, self).setUp()
        self.data = {'id': 1,
                     'name': 'Sample Project',
                     'short_name': 'sampleapp',
                     'description': 'Long Description',
                     'allow_anonymous_contributors': 'True',
                     'category_id': 1,
                     'long_description': 'Long Description\n================',
                     'hidden': 'false',
                     'btn': 'Save'}
        self.editor = {'editor': 'Some HTML code!'}

    @with_context
    def test_app_update_name(self):
        self.register()
        self.new_application()
        short_name = 'sampleapp'

        url = "/app/%s/update" % short_name

        self.data['name'] = 'New'

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(app_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == 'name', log.attribute
            assert log.old_value == 'Sample Project', log.old_value
            assert log.new_value == self.data['name'], log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_app_update_short_name(self):
        self.register()
        self.new_application()
        short_name = 'newshort_name'

        url = "/app/sampleapp/update"

        self.data['short_name'] = 'newshort_name'

        res = self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(app_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == 'short_name', log.attribute
            assert log.old_value == 'sampleapp', log.old_value
            assert log.new_value == self.data['short_name'], log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_app_description(self):
        self.register()
        self.new_application()
        short_name = 'sampleapp'

        url = "/app/%s/update" % short_name

        attribute = 'description'

        new_string = 'New Something'

        old_value = self.data[attribute]

        self.data[attribute] = new_string

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(app_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == self.data[attribute], log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id


    @with_context
    def test_app_allow_anonymous_contributors(self):
        self.register()
        self.new_application()
        short_name = 'sampleapp'

        url = "/app/%s/update" % short_name

        attribute = 'allow_anonymous_contributors'

        new_string = 'False'

        old_value = self.data[attribute]

        self.data[attribute] = new_string

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(app_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == self.data[attribute], log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_app_hidden(self):
        self.register()
        self.new_application()
        short_name = 'sampleapp'

        url = "/app/%s/update" % short_name

        attribute = 'hidden'

        new_string = True

        old_value = self.data[attribute]

        self.data[attribute] = new_string

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(app_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, log.old_value
            assert bool(log.new_value) == self.data[attribute], log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id


    @with_context
    def test_app_long_description(self):
        self.register()
        self.new_application()
        short_name = 'sampleapp'

        url = "/app/%s/update" % short_name

        attribute = 'long_description'

        new_string = 'New long desc'

        old_value = self.data[attribute]

        self.data[attribute] = new_string

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(app_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == self.data[attribute], log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id


    @with_context
    def test_app_password(self):
        self.register()
        self.new_application()
        short_name = 'sampleapp'

        url = "/app/%s/update" % short_name

        attribute = 'password'

        new_string = 'new password'

        old_value = 'null'

        self.data[attribute] = new_string

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(app_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == 'passwd_hash', log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value != None, log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    @patch('pybossa.forms.validator.requests.get')
    def test_app_webhook(self, mock):
        html_request = FakeRequest(json.dumps(self.data), 200,
                                   {'content-type': 'application/json'})
        mock.return_value = html_request

        self.register()
        self.new_application()
        short_name = 'sampleapp'

        url = "/app/%s/update" % short_name

        attribute = 'webhook'

        new_string = 'http://google.com'

        old_value = ''

        self.data[attribute] = new_string

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(app_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == self.data[attribute], log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_app_task_presenter(self):
        self.register()
        self.new_application()
        short_name = 'sampleapp'

        url = "/app/%s/tasks/taskpresentereditor" % short_name

        attribute = 'editor'

        new_string = 'new code'

        old_value = None

        self.editor[attribute] = new_string

        self.app.post(url, data=self.editor, follow_redirects=True)

        logs = auditlog_repo.filter_by(app_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == 'task_presenter', log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == new_string, log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id
