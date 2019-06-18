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
import StringIO
from default import with_context
from pybossa.util import unicode_csv_reader
from factories import UserFactory
from helper import web
from factories import TaskFactory, ProjectFactory, TaskRunFactory, UserFactory
from mock import patch
from pybossa.jobs import export_all_users


class TestExportUsers(web.Helper):

    exportable_attributes = ('id', 'name', 'fullname', 'email_addr',
                             'created', 'locale', 'admin')

    def create_project_and_tasks(self):
        owner = UserFactory.create(id=333)
        project = ProjectFactory.create(owner=owner)
        TaskFactory.create(project=project, n_answers=20)
        return project

    def contribute(self, project):
        res = self.app.get('api/project/%s/newtask' % project.id)
        data = json.loads(res.data)
        data = {'project_id': project.id,
                'task_id': data['id'],
                'info': {}}
        res = self.app.post('api/taskrun', data=json.dumps(data))

    @with_context
    @patch('pybossa.jobs.send_mail')
    def test_json_contains_all_attributes(self, send):
        self.register()
        self.signin()
        project = self.create_project_and_tasks()
        self.contribute(project)

        export_all_users('json', 'hello@c.com')
        args, _ = send.call_args
        data = json.loads(args[0]['attachments'][0].data)

        for attribute in self.exportable_attributes:
            assert attribute in data[0], data

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('pybossa.api.pwd_manager.ProjectPasswdManager.password_needed')
    def test_json_returns_all_users(self, password_needed, send):
        password_needed.return_value = False
        restricted = UserFactory.create(restrict=True, id=5000014)
        self.register(fullname="Manolita")
        project = self.create_project_and_tasks()
        self.signin()
        self.contribute(project)
        self.signout()
        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.signin(email="juan@juan.com", password="juan")
        self.contribute(project)
        self.signout()
        self.register(fullname="Juan Jose2", name="juan2",
                      email="juan2@juan.com", password="juan2")
        self.signin(email="juan2@juan.com", password="juan2")
        self.contribute(project)
        self.signout()
        self.signin()

        export_all_users('json', 'hello@c.com')
        args, _ = send.call_args
        data = args[0]['attachments'][0].data
        json_data = json.loads(data)

        assert "Juan Jose" in data, data
        assert "Manolita" in data, data
        assert "Juan Jose2" in data, data
        assert len(json_data) == 4 # all users report returns user_1@test.com
        assert restricted.name not in data, data

    @with_context
    @patch('pybossa.jobs.send_mail')
    def test_csv_contains_all_attributes(self, send):
        self.register()
        self.signin()

        restricted = UserFactory.create(restrict=True, id=5000015)

        export_all_users('csv', 'hello@c.com')
        args, _ = send.call_args
        data = args[0]['attachments'][0].data

        for attribute in self.exportable_attributes:
            assert attribute in data, data
        assert restricted.name not in data, data

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('pybossa.api.pwd_manager.ProjectPasswdManager.password_needed')
    def test_csv_returns_all_users(self, password_needed, send):
        password_needed.return_value = False
        restricted = UserFactory.create(restrict=True, id=5000016)
        self.register(fullname="Manolita")
        project = self.create_project_and_tasks()
        self.signin()
        self.contribute(project)
        self.signout()

        self.register(fullname="Juan Jose", name="juan",
                      email="juan@juan.com", password="juan")
        self.signin(email="juan@juan.com", password="juan")
        self.contribute(project)
        self.signout()

        self.register(fullname="Juan Jose2", name="juan2",
                      email="juan2@juan.com", password="juan2")
        self.signin(email="juan2@juan.com", password="juan2")
        self.contribute(project)
        self.signout()
        self.signin()

        export_all_users('csv', 'hello@c.com')
        args, _ = send.call_args
        data = args[0]['attachments'][0].data

        assert restricted.name not in data
        csv_content = StringIO.StringIO(data)
        csvreader = unicode_csv_reader(csv_content)
        # number of users is -1 because the first row in csv are the headers
        number_of_users = -1
        for row in csvreader:
            number_of_users += 1

        assert number_of_users == 4, number_of_users # user report returning all users also returns user1@test.com
