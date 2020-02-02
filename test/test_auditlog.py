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
from default import db, Test, with_context
from collections import namedtuple
from factories import ProjectFactory, TaskFactory, UserFactory, CategoryFactory
from helper import web

from pybossa.repositories import UserRepository
from pybossa.repositories import AuditlogRepository
from mock import patch, MagicMock

auditlog_repo = AuditlogRepository(db)
user_repo = UserRepository(db)


FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])

class TestAuditlogAPI(Test):

    @with_context
    def test_project_create(self):
        """Test Auditlog API project create works."""
        CategoryFactory.create()
        user = UserFactory.create()

        data = {'name': 'New Name',
                'short_name': 'new_short_name',
                'description': 'new_description',
                'long_description': 'new_long_description',
                'allow_anonymous_contributors': False,
                'zip_download': True
                }
        url = '/api/project?api_key=%s' % (user.api_key)
        self.app.post(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(project_short_name='new_short_name')

        assert len(logs) == 1, logs
        for log in logs:
            assert log.user_id == user.id, log.user_id
            assert log.user_name == user.name, log.user_name
            assert log.project_short_name == 'new_short_name', log.project_short_name
            assert log.caller == 'api', log.caller
            assert log.action == 'create', log.action
            assert log.attribute == 'project', log.attribute
            assert log.old_value == 'Nothing', log.old_value
            assert log.new_value == 'New project', log.new_value

    @with_context
    def test_project_delete(self):
        """Test Auditlog API project create works."""
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        project_short_name = project.short_name

        url = '/api/project/%s?api_key=%s' % (project.id, user.api_key)
        self.app.delete(url)
        logs = auditlog_repo.filter_by(project_short_name=project_short_name)

        assert len(logs) == 1, logs
        for log in logs:
            assert log.user_id == user.id, log.user_id
            assert log.user_name == user.name, log.user_name
            assert log.project_short_name == project_short_name, log.project_short_name
            assert log.caller == 'api', log.caller
            assert log.action == 'delete', log.action
            assert log.attribute == 'project', log.attribute
            assert log.old_value == 'Saved', log.old_value
            assert log.new_value == 'Deleted', log.new_value

    @with_context
    def test_project_update_attributes(self):
        """Test Auditlog API project update attributes works."""
        project = ProjectFactory.create(info=dict(list=[0]))

        data = {'name': 'New Name',
                'short_name': 'new_short_name',
                'description': 'new_description',
                'long_description': 'new_long_description',
                'allow_anonymous_contributors': False,
                'info': {'list': [1]}
                }
        attributes = list(data.keys())
        attributes.append('list')
        url = '/api/project/%s?api_key=%s' % (project.id, project.owner.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(project_id=project.id)

        assert len(logs) == 6, (len(logs), logs)
        for log in logs:
            assert log.user_id == project.owner_id, log.user_id
            assert log.user_name == project.owner.name, log.user_name
            assert log.project_short_name == project.short_name, log.project_short_name
            assert log.action == 'update', log.action
            assert log.caller == 'api', log.caller
            assert log.attribute in attributes, (log.attribute, attributes)
            if log.attribute != 'list':
                msg = "%s != %s" % (data[log.attribute], log.new_value)
                assert str(data[log.attribute]) == log.new_value, msg
            else:
                msg = "%s != %s" % (data['info'][log.attribute], log.new_value)
                assert data['info'][log.attribute] == json.loads(log.new_value), msg

    @with_context
    def test_project_update_attributes_admin(self):
        """Test Auditlog API project update attributes works for admins."""
        project = ProjectFactory.create()
        admin = UserFactory.create(admin=True)

        data = {'name': 'New Name',
                'short_name': 'new_short_name',
                'description': 'new_description',
                'long_description': 'new_long_description',
                'allow_anonymous_contributors': False,
                }
        attributes = list(data.keys())
        url = '/api/project/%s?api_key=%s' % (project.id, admin.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(project_id=project.id)

        assert len(logs) == 5, logs
        for log in logs:
            assert log.user_id == admin.id, log.user_id
            assert log.user_name == admin.name, log.user_name
            assert log.project_short_name == project.short_name, log.project_short_name
            assert log.action == 'update', log.action
            assert log.caller == 'api', log.caller
            assert log.attribute in attributes, log.attribute
            msg = "%s != %s" % (data[log.attribute], log.new_value)
            assert str(data[log.attribute]) == log.new_value, msg

    @with_context
    def test_project_update_attributes_non_owner(self):
        """Test Auditlog API project update attributes works for non owners."""
        project = ProjectFactory.create()
        user = UserFactory.create()

        data = {'name': 'New Name',
                'short_name': 'new_short_name',
                'description': 'new_description',
                'long_description': 'new_long_description',
                'allow_anonymous_contributors': False,
                }
        url = '/api/project/%s?api_key=%s' % (project.id, user.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(project_id=project.id)

        assert len(logs) == 0, logs

    @with_context
    def test_project_update_task_presenter(self):
        """Test Auditlog API project update info task_presenter works."""
        project = ProjectFactory.create()

        owner_id = project.owner.id
        owner_name = project.owner.name
        data = {'info': {'task_presenter': 'new'}}
        url = '/api/project/%s?api_key=%s' % (project.id, project.owner.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(project_id=project.id)

        assert len(logs) == 1, logs
        for log in logs:
            assert log.user_id == owner_id, log.user_id
            assert log.user_name == owner_name, log.user_name
            assert log.project_short_name == project.short_name, log.project_short_name
            assert log.action == 'update', log.action
            assert log.caller == 'api', log.caller
            assert log.attribute == 'task_presenter', log.attribute
            msg = "%s != %s" % (data['info']['task_presenter'], log.new_value)
            assert data['info']['task_presenter'] == log.new_value, msg

    @with_context
    def test_project_update_scheduler(self):
        """Test Auditlog API project update info scheduler works."""
        project = ProjectFactory.create()

        owner_id = project.owner.id
        owner_name = project.owner.name
        data = {'info': {'sched': 'depth_first'}}
        url = '/api/project/%s?api_key=%s' % (project.id, project.owner.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(project_id=project.id)

        assert len(logs) == 1, logs
        for log in logs:
            assert log.user_id == owner_id, log.user_id
            assert log.user_name == owner_name, log.user_name
            assert log.project_short_name == project.short_name, log.project_short_name
            assert log.action == 'update', log.action
            assert log.caller == 'api', log.caller
            assert log.attribute == 'sched', log.attribute
            msg = "%s != %s" % (data['info']['sched'], log.new_value)
            assert data['info']['sched'] == log.new_value, msg

    @with_context
    def test_project_update_two_info_objects(self):
        """Test Auditlog API project update two info objects works."""
        project = ProjectFactory.create()

        owner_id = project.owner.id
        owner_name = project.owner.name
        data = {'info': {'sched': 'depth_first', 'task_presenter': 'new'}}
        attributes = list(data['info'].keys())
        url = '/api/project/%s?api_key=%s' % (project.id, project.owner.api_key)
        self.app.put(url, data=json.dumps(data))
        logs = auditlog_repo.filter_by(project_id=project.id)

        assert len(logs) == 2, logs
        for log in logs:
            assert log.user_id == owner_id, log.user_id
            assert log.user_name == owner_name, log.user_name
            assert log.project_short_name == project.short_name, log.project_short_name
            assert log.action == 'update', log.action
            assert log.caller == 'api', log.caller
            assert log.attribute in attributes, log.attribute
            msg = "%s != %s" % (data['info'][log.attribute], log.new_value)
            assert data['info'][log.attribute] == log.new_value, msg


class TestAuditlogWEB(web.Helper):

    data = {}
    editor = {}

    def setUp(self):
        super(TestAuditlogWEB, self).setUp()
        self.data = {'id': 1,
                     'name': 'Sample Project',
                     'short_name': 'sampleapp',
                     'description': 'Description',
                     'allow_anonymous_contributors': 'true',
                     'category_id': 1,
                     'long_description': 'Long Description\n================',
                     'btn': 'Save'}
        self.editor = {'editor': 'Some HTML code!'}

    @with_context
    def test_project_create(self):
        self.register()
        self.new_project()
        short_name = 'sampleapp'

        logs = auditlog_repo.filter_by(project_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == 'project', log.attribute
            assert log.old_value == 'Nothing', log.old_value
            assert log.new_value == 'New project', log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'create', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_project_create(self):
        self.register()
        self.new_project()
        self.delete_project()
        short_name = 'sampleapp'

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == 'project', log.attribute
            assert log.old_value == 'Saved', log.old_value
            assert log.new_value == 'Deleted', log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'delete', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_project_update_name(self):
        self.register()
        self.new_project()
        short_name = 'sampleapp'

        url = "/project/%s/update" % short_name

        self.data['name'] = 'New'
        self.data['zip_download'] = True

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
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
    def test_project_update_short_name(self):
        self.register()
        self.new_project()
        short_name = 'newshort_name'

        url = "/project/sampleapp/update"

        self.data['short_name'] = 'newshort_name'
        self.data['zip_download'] = True

        res = self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name)
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
    def test_project_description(self):
        self.register()
        self.new_project()
        short_name = 'sampleapp'

        url = "/project/%s/update" % short_name

        attribute = 'description'

        new_string = 'New Something'

        old_value = self.data[attribute]

        self.data[attribute] = new_string
        self.data['zip_download'] = True

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
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
    def test_project_allow_anonymous_contributors(self):
        self.register()
        self.new_project()
        short_name = 'sampleapp'

        url = "/project/%s/update" % short_name

        attribute = 'allow_anonymous_contributors'

        new_value = 'false'

        old_value = self.data[attribute]

        self.data[attribute] = new_value

        self.data['zip_download'] = True

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
        for log in logs:
            print(log)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value.capitalize(), log.old_value
            assert log.new_value == new_value.capitalize(), log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_project_published(self):
        owner = UserFactory.create(email_addr='a@a.com', pro=True)
        owner.set_password('1234')
        user_repo.save(owner)
        project = ProjectFactory.create(owner=owner, published=False)
        self.signin(email='a@a.com', password='1234')
        TaskFactory.create(project=project)
        short_name = project.short_name

        url = "/project/%s/publish" % short_name

        attribute = 'published'

        new_string = 'true'

        old_value = 'false'

        self.data[attribute] = new_string

        self.app.post(url, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, (log.old_value, old_value)
            assert log.new_value == self.data[attribute], log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == owner.name, log.user_name
            assert log.user_id == owner.id, log.user_id

    @with_context
    def test_project_long_description(self):
        self.register()
        self.new_project()
        short_name = 'sampleapp'

        url = "/project/%s/update" % short_name

        attribute = 'long_description'

        new_string = 'New long desc'

        old_value = self.data[attribute]

        self.data[attribute] = new_string
        self.data['zip_download'] = True

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
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
    def test_project_password(self):
        self.register()
        self.new_project()
        short_name = 'sampleapp'

        url = "/project/%s/update" % short_name

        attribute = 'password'

        new_string = 'new password'

        old_value = None

        self.data[attribute] = new_string
        self.data['protect'] = True
        self.data['zip_download'] = True

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
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
    def test_project_webhook(self, mock):
        html_request = FakeRequest(json.dumps(self.data), 200,
                                   {'content-type': 'projectlication/json'})
        mock.return_value = html_request

        self.register()
        self.new_project()
        short_name = 'sampleapp'

        url = "/project/%s/update" % short_name

        attribute = 'webhook'

        new_string = 'http://google.com'

        old_value = ''

        self.data[attribute] = new_string
        self.data['zip_download'] = True

        self.app.post(url, data=self.data, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
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
    def test_project_task_presenter(self):
        self.register()
        self.new_project()
        short_name = 'sampleapp'

        url = "/project/%s/tasks/taskpresentereditor" % short_name

        attribute = 'editor'

        new_string = 'new code'

        old_value = None

        self.editor[attribute] = new_string

        self.app.post(url, data=self.editor, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == 'task_presenter', log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == new_string, log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_project_task_scheduler(self):
        self.register()
        self.new_project()
        short_name = 'sampleapp'

        url = "/project/%s/tasks/scheduler" % short_name

        attribute = 'sched'

        new_string = 'depth_first'

        old_value = 'default'

        self.app.post(url, data={'sched': new_string}, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == 'sched', log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == new_string, log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_project_task_priority(self):
        self.register()
        self.new_project()
        self.new_task(1)
        short_name = 'sampleapp'

        url = "/project/%s/tasks/priority" % short_name

        attribute = 'task.priority_0'

        new_string = json.dumps({'task_id': 1, 'task_priority_0': 0.5})

        old_value = json.dumps({'task_id': 1, 'task_priority_0': 0.0})

        self.app.post(url, data={'task_ids': '1', 'priority_0': '0.5'}, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == new_string, log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_project_task_priority_two_tasks(self):
        self.register()
        self.new_project()
        self.new_task(1)
        self.new_task(1)
        short_name = 'sampleapp'

        url = "/project/%s/tasks/priority" % short_name

        attribute = 'task.priority_0'

        self.app.post(url, data={'task_ids': '1,2', 'priority_0': '0.5'}, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
        assert len(logs) == 2, logs
        id = 1
        for log in logs:
            new_string = json.dumps({'task_id': id, 'task_priority_0': 0.5})
            old_value = json.dumps({'task_id': id, 'task_priority_0': 0.0})

            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == new_string, log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id
            id = id +1

    @with_context
    def test_project_task_redundancy(self):
        self.register()
        self.new_project()
        self.new_task(1)
        short_name = 'sampleapp'

        url = "/project/%s/tasks/redundancy" % short_name

        attribute = 'task.n_answers'

        new_string = '10'
        # Depends on each specific task, so old value will be non-avaliable
        old_value = 'N/A'

        self.app.post(url, data={'n_answers': '10'}, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == new_string, log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'update', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_project_auditlog_autoimporter_create(self):
        self.register()
        self.new_project()
        self.new_task(1)
        short_name = 'sampleapp'

        url = "/project/%s/tasks/autoimporter" % short_name
        data = {'form_name': 'csv', 'csv_url': 'http://fakeurl.com'}

        self.app.post(url, data=data, follow_redirects=True)

        attribute = 'autoimporter'

        new_value = '{"type": "csv", "csv_url": "http://fakeurl.com"}'

        old_value = 'Nothing'

        logs = auditlog_repo.filter_by(project_short_name=short_name, offset=1)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == new_value, log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'create', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_project_auditlog_autoimporter_delete(self):
        self.register()
        owner = user_repo.get(1)
        autoimporter = {'type': 'csv', 'csv_url': 'http://fakeurl.com'}
        project = ProjectFactory.create(owner=owner, info={'autoimporter': autoimporter})
        short_name = project.short_name

        attribute = 'autoimporter'

        old_value = json.dumps(autoimporter)

        new_value = 'Nothing'

        url = "/project/%s/tasks/autoimporter/delete" % short_name
        self.app.post(url, data={}, follow_redirects=True)

        logs = auditlog_repo.filter_by(project_short_name=short_name)
        assert len(logs) == 1, logs
        for log in logs:
            assert log.attribute == attribute, log.attribute
            assert log.old_value == old_value, log.old_value
            assert log.new_value == new_value, log.new_value
            assert log.caller == 'web', log.caller
            assert log.action == 'delete', log.action
            assert log.user_name == 'johndoe', log.user_name
            assert log.user_id == 1, log.user_id

    @with_context
    def test_project_auditlog_access_anon(self):
        # Admin
        self.register()
        self.new_project()
        self.new_task(1)
        short_name = 'sampleapp'
        self.signout()

        url = "/project/%s/auditlog" % short_name

        res = self.app.get(url, follow_redirects=True)
        assert "Sign in" in str(res.data), res.data

    @with_context
    def test_project_auditlog_access_owner(self):
        # Admin
        self.register()
        self.signout()
        # User
        self.register(name="Iser")
        self.new_project()
        self.new_task(1)
        short_name = 'sampleapp'

        url = "/project/%s/auditlog" % short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 403, res.status_code

    @with_context
    def test_project_auditlog_access_pro(self):
        # Admin
        self.register()
        self.signout()
        # User
        self.register(name="Iser")
        self.new_project()
        self.new_task(1)
        short_name = 'sampleapp'

        user = user_repo.filter_by(name="Iser")[0]
        user.pro = True
        user_repo.save(user)

        url = "/project/%s/auditlog" % short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 200, res.status_code

    @with_context
    def test_project_auditlog_access_admin(self):
        # Admin
        self.register()
        self.signout()
        # User
        self.register(name="user", password="user")
        self.new_project()
        self.new_task(1)
        self.signout()
        # Access as admin
        self.signin()
        short_name = 'sampleapp'

        url = "/project/%s/auditlog" % short_name

        res = self.app.get(url, follow_redirects=True)
        assert  res.status_code == 200, res.status_code
