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
from mock import patch, call
from default import db, with_context
from nose.tools import assert_equal, assert_raises
from test_api import TestAPI

from factories import (ProjectFactory, TaskFactory, TaskRunFactory, AnonymousTaskRunFactory, UserFactory,
                       CategoryFactory)

from pybossa.repositories import ProjectRepository
from pybossa.repositories import TaskRepository
project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)

class TestProjectAPI(TestAPI):

    @with_context
    def test_project_query(self):
        """ Test API project query"""
        ProjectFactory.create(info={'total': 150})
        res = self.app.get('/api/project')
        data = json.loads(res.data)
        assert len(data) == 1, data
        project = data[0]
        assert project['info']['total'] == 150, data

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # Test a non-existant ID
        res = self.app.get('/api/project/0')
        err = json.loads(res.data)
        assert res.status_code == 404, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'project', err
        assert err['exception_cls'] == 'NotFound', err
        assert err['action'] == 'GET', err


    def test_hidden_project(self):
        """ Test API hidden project works. """
        ProjectFactory.create(hidden=1)
        res = self.app.get('/api/project')
        data = json.loads(res.data)

        err_msg = "There should be zero projects listed."
        assert len(data) == 0, err_msg
        err_msg = "It should return 200 with an empty object"
        assert res.status_code == 200, err_msg

        # Now we add a second project that it is not hidden
        ProjectFactory.create(info={'hello': 'world'})
        res = self.app.get('/api/project')
        data = json.loads(res.data)

        err_msg = "There should be only one project listed."
        assert len(data) == 1, err_msg
        err_msg = "It should return 200 with one project"
        assert res.status_code == 200, err_msg
        project = data[0]
        assert project['info']['hello'] == 'world', err_msg


    @with_context
    def test_query_project(self):
        """Test API query for project endpoint works"""
        ProjectFactory.create(short_name='test-app', name='My New Project')
        # Test for real field
        res = self.app.get("/api/project?short_name=test-app", follow_redirects=True)
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data

        # Valid field but wrong value
        res = self.app.get("/api/project?short_name=wrongvalue")
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/project?short_name=test-app&name=My New Project')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data
        assert data[0]['name'] == 'My New Project', data


    @with_context
    def test_project_post(self):
        """Test API project creation and auth"""
        users = UserFactory.create_batch(2)
        CategoryFactory.create()
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project',
            description='description',
            owner_id=1,
            long_description=u'Long Description\n================')
        data = json.dumps(data)
        # no api-key
        res = self.app.post('/api/project', data=data)
        assert_equal(res.status, '401 UNAUTHORIZED',
                     'Should not be allowed to create')
        # now a real user
        res = self.app.post('/api/project?api_key=' + users[1].api_key,
                            data=data)
        out = project_repo.get_by(name=name)
        assert out, out
        assert_equal(out.short_name, 'xxxx-project'), out
        assert_equal(out.owner.name, 'user2')
        id_ = out.id

        # now a real user with headers auth
        headers = [('Authorization', users[1].api_key)]
        new_project = dict(
            name=name + '2',
            short_name='xxxx-project2',
            description='description2',
            owner_id=1,
            long_description=u'Long Description\n================')
        new_project = json.dumps(new_project)
        res = self.app.post('/api/project', headers=headers,
                            data=new_project)
        out = project_repo.get_by(name=name + '2')
        assert out, out
        assert_equal(out.short_name, 'xxxx-project2'), out
        assert_equal(out.owner.name, 'user2')
        ## Test that a default category is assigned to the project
        assert out.category_id, "No category assigned to project"
        id_ = out.id

        # test re-create should fail
        res = self.app.post('/api/project?api_key=' + users[1].api_key,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == "DBIntegrityError", err

        # test create with non-allowed fields should fail
        data = dict(name='fail', short_name='fail', link='hateoas', wrong=15)
        res = self.app.post('/api/project?api_key=' + users[1].api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = "ValueError exception should be raised"
        assert res.status_code == 415, err
        assert err['action'] == 'POST', err
        assert err['status'] == 'failed', err
        assert err['exception_cls'] == "ValueError", err_msg
        # Now with a JSON object but not valid
        data = json.dumps(data)
        res = self.app.post('/api/project?api_key=' + users[1].api_key,
                            data=data)
        err = json.loads(res.data)
        err_msg = "TypeError exception should be raised"
        assert err['action'] == 'POST', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == "TypeError", err_msg
        assert res.status_code == 415, err_msg

        # test update
        data = {'name': 'My New Title', 'links': 'hateoas'}
        datajson = json.dumps(data)
        ## anonymous
        res = self.app.put('/api/project/%s' % id_, data=data)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Unauthorized', error

        ### real user but not allowed as not owner!
        non_owner = UserFactory.create()
        url = '/api/project/%s?api_key=%s' % (id_, non_owner.api_key)
        res = self.app.put(url, data=datajson)
        error_msg = 'Should not be able to update projects of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Forbidden', error

        res = self.app.put('/api/project/%s?api_key=%s' % (id_, users[1].api_key),
                           data=datajson)

        # with hateoas links
        assert_equal(res.status, '200 OK', res.data)
        out2 = project_repo.get(id_)
        assert_equal(out2.name, data['name'])
        out = json.loads(res.data)
        assert out.get('status') is None, error
        assert out.get('id') == id_, error

        # without hateoas links
        del data['links']
        newdata = json.dumps(data)
        res = self.app.put('/api/project/%s?api_key=%s' % (id_, users[1].api_key),
                           data=newdata)

        assert_equal(res.status, '200 OK', res.data)
        out2 = project_repo.get(id_)
        assert_equal(out2.name, data['name'])
        out = json.loads(res.data)
        assert out.get('status') is None, error
        assert out.get('id') == id_, error

        # With wrong id
        res = self.app.put('/api/project/5000?api_key=%s' % users[1].api_key,
                           data=datajson)
        assert_equal(res.status, '404 NOT FOUND', res.data)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'NotFound', error

        # With fake data
        data['algo'] = 13
        datajson = json.dumps(data)
        res = self.app.put('/api/project/%s?api_key=%s' % (id_, users[1].api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err

        # With empty fields
        data.pop('algo')
        data['name'] = None
        datajson = json.dumps(data)
        res = self.app.put('/api/project/%s?api_key=%s' % (id_, users[1].api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'DBIntegrityError', err

        data['name'] = ''
        datajson = json.dumps(data)
        res = self.app.put('/api/project/%s?api_key=%s' % (id_, users[1].api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'DBIntegrityError', err

        data['name'] = 'something'
        data['short_name'] = ''
        datajson = json.dumps(data)
        res = self.app.put('/api/project/%s?api_key=%s' % (id_, users[1].api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'DBIntegrityError', err


        # With not JSON data
        datajson = data
        res = self.app.put('/api/project/%s?api_key=%s' % (id_, users[1].api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # With wrong args in the URL
        data = dict(
            name=name,
            short_name='xxxx-project',
            long_description=u'Long Description\n================')

        datajson = json.dumps(data)
        res = self.app.put('/api/project/%s?api_key=%s&search=select1' % (id_, users[1].api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # test delete
        ## anonymous
        res = self.app.delete('/api/project/%s' % id_, data=data)
        error_msg = 'Anonymous should not be allowed to delete'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'project', error
        ### real user but not allowed as not owner!
        url = '/api/project/%s?api_key=%s' % (id_, non_owner.api_key)
        res = self.app.delete(url, data=datajson)
        error_msg = 'Should not be able to delete projects of others'
        assert_equal(res.status, '403 FORBIDDEN', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'project', error

        url = '/api/project/%s?api_key=%s' % (id_, users[1].api_key)
        res = self.app.delete(url, data=datajson)

        assert_equal(res.status, '204 NO CONTENT', res.data)

        # delete a project that does not exist
        url = '/api/project/5000?api_key=%s' % users[1].api_key
        res = self.app.delete(url, data=datajson)
        error = json.loads(res.data)
        assert res.status_code == 404, error
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'project', error
        assert error['exception_cls'] == 'NotFound', error

        # delete a project that does not exist
        url = '/api/project/?api_key=%s' % users[1].api_key
        res = self.app.delete(url, data=datajson)
        assert res.status_code == 404, error


    @with_context
    def test_project_post_invalid_short_name(self):
        """Test API project POST returns error if short_name is invalid (i.e. is
            a name used by the Flask app as a URL endpoint"""
        users = UserFactory.create_batch(2)
        CategoryFactory.create()
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='new',
            description='description',
            owner_id=1,
            long_description=u'Long Description\n================')
        data = json.dumps(data)
        res = self.app.post('/api/project?api_key=' + users[1].api_key,
                            data=data)
        error = json.loads(res.data)
        assert res.status_code == 415, res.status_code
        assert error['status'] == 'failed', error
        assert error['action'] == 'POST', error
        assert error['target'] == 'project', error
        assert error['exception_cls'] == 'ValueError', error
        message = "Project short_name is not valid, as it's used by the system."
        assert error['exception_msg'] == message, error


    @with_context
    def test_project_put_invalid_short_name(self):
        """Test API project PUT returns error if short_name is invalid (i.e. is
            a name used by the Flask app as a URL endpoint"""
        user = UserFactory.create()
        CategoryFactory.create()
        project = ProjectFactory.create(owner=user)
        name = u'XXXX Project'
        data = {'short_name': 'new'}
        datajson = json.dumps(data)
        res = self.app.put('/api/project/%s?api_key=%s' % (project.id, user.api_key),
                            data=datajson)
        error = json.loads(res.data)
        assert res.status_code == 415, res.status_code
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['target'] == 'project', error
        assert error['exception_cls'] == 'ValueError', error
        message = "Project short_name is not valid, as it's used by the system."
        assert error['exception_msg'] == message, error


    @with_context
    def test_admin_project_post(self):
        """Test API project update/delete for ADMIN users"""
        admin = UserFactory.create()
        assert admin.admin
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user, short_name='xxxx-project')

        # test update
        data = {'name': 'My New Title'}
        datajson = json.dumps(data)
        ### admin user but not owner!
        url = '/api/project/%s?api_key=%s' % (project.id, admin.api_key)
        res = self.app.put(url, data=datajson, follow_redirects=True)

        assert_equal(res.status, '200 OK', res.data)
        out2 = project_repo.get(project.id)
        assert_equal(out2.name, data['name'])

        # PUT with not JSON data
        res = self.app.put(url, data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'project', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'ValueError', err

        # PUT with not allowed args
        res = self.app.put(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'project', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # PUT with fake data
        data['wrongfield'] = 13
        res = self.app.put(url, data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'project', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'TypeError', err
        data.pop('wrongfield')

        # test delete
        url = '/api/project/%s?api_key=%s' % (project.id, admin.api_key)
        # DELETE with not allowed args
        res = self.app.delete(url + "&foo=bar", data=json.dumps(data))
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'project', err
        assert err['action'] == 'DELETE', err
        assert err['exception_cls'] == 'AttributeError', err

        ### DELETE success real user  not owner!
        res = self.app.delete(url, data=json.dumps(data))
        assert_equal(res.status, '204 NO CONTENT', res.data)

    @with_context
    def test_user_progress_anonymous(self):
        """Test API userprogress as anonymous works"""
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        tasks = TaskFactory.create_batch(2, project=project)
        taskruns = []
        for task in tasks:
            taskruns.extend(AnonymousTaskRunFactory.create_batch(2, task=task))

        res = self.app.get('/api/project/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)

        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "The reported number of done tasks is wrong"
        assert len(taskruns) == data['done'], data

        # Add a new TaskRun and check again
        taskrun = AnonymousTaskRunFactory.create(task=tasks[0], info={'answer': u'hello'})

        res = self.app.get('/api/project/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "Number of done tasks is wrong: %s" % len(taskruns)
        assert len(taskruns) + 1 == data['done'], error_msg

    @with_context
    def test_user_progress_authenticated_user(self):
        """Test API userprogress as an authenticated user works"""
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        tasks = TaskFactory.create_batch(2, project=project)
        taskruns = []
        for task in tasks:
            taskruns.extend(TaskRunFactory.create_batch(2, task=task, user=user))

        url = '/api/project/1/userprogress?api_key=%s' % user.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        url = '/api/project/%s/userprogress?api_key=%s' % (project.short_name, user.api_key)
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        url = '/api/project/5000/userprogress?api_key=%s' % user.api_key
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        url = '/api/project/userprogress?api_key=%s' % user.api_key
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        error_msg = "The reported number of done tasks is wrong"
        assert len(taskruns) == data['done'], error_msg

        # Add a new TaskRun and check again
        taskrun = TaskRunFactory.create(task=tasks[0], info={'answer': u'hello'}, user=user)

        url = '/api/project/1/userprogress?api_key=%s' % user.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "Number of done tasks is wrong: %s" % len(taskruns)
        assert len(taskruns) + 1 == data['done'], error_msg


    @with_context
    def test_delete_project_cascade(self):
        """Test API delete project deletes associated tasks and taskruns"""
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(2, project=project)
        task_runs = TaskRunFactory.create_batch(2, project=project)
        url = '/api/project/%s?api_key=%s' % (1, project.owner.api_key)
        self.app.delete(url)

        tasks = task_repo.filter_tasks_by(project_id=project.id)
        assert len(tasks) == 0, "There should not be any task"

        task_runs = task_repo.filter_task_runs_by(project_id=project.id)
        assert len(task_runs) == 0, "There should not be any task run"


    @with_context
    def test_newtask_allow_anonymous_contributors(self):
        """Test API get a newtask - allow anonymous contributors"""
        project = ProjectFactory.create()
        user = UserFactory.create()
        tasks = TaskFactory.create_batch(2, project=project, info={'question': 'answer'})

        # All users are allowed to participate by default
        # As Anonymous user
        url = '/api/project/%s/newtask' % project.id
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.project_id is different from the project.id"
        assert task['project_id'] == project.id, err_msg
        err_msg = "There should not be an error message"
        assert task['info'].get('error') is None, err_msg
        err_msg = "There should be a question"
        assert task['info'].get('question') == 'answer', err_msg

        # As registered user
        url = '/api/project/%s/newtask?api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.project_id is different from the project.id"
        assert task['project_id'] == project.id, err_msg
        err_msg = "There should not be an error message"
        assert task['info'].get('error') is None, err_msg
        err_msg = "There should be a question"
        assert task['info'].get('question') == 'answer', err_msg

        # Now only allow authenticated users
        project.allow_anonymous_contributors = False
        project_repo.update(project)

        # As Anonymous user
        url = '/api/project/%s/newtask' % project.id
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.project_id should be null"
        assert task['project_id'] is None, err_msg
        err_msg = "There should be an error message"
        err = "This project does not allow anonymous contributors"
        assert task['info'].get('error') == err, err_msg
        err_msg = "There should not be a question"
        assert task['info'].get('question') is None, err_msg

        # As registered user
        url = '/api/project/%s/newtask?api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url, follow_redirects=True)
        task = json.loads(res.data)
        err_msg = "The task.project_id is different from the project.id"
        assert task['project_id'] == project.id, err_msg
        err_msg = "There should not be an error message"
        assert task['info'].get('error') is None, err_msg
        err_msg = "There should be a question"
        assert task['info'].get('question') == 'answer', err_msg


    @with_context
    def test_newtask(self):
        """Test API project new_task method and authentication"""
        project = ProjectFactory.create()
        TaskFactory.create_batch(2, project=project)
        user = UserFactory.create()

        # anonymous
        # test getting a new task
        res = self.app.get('/api/project/%s/newtask' % project.id)
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['project_id'], project.id)

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # as a real user
        url = '/api/project/%s/newtask?api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url)
        assert res, res
        task = json.loads(res.data)
        assert_equal(task['project_id'], project.id)

        # Get NotFound for an non-existing project
        url = '/api/project/5000/newtask'
        res = self.app.get(url)
        err = json.loads(res.data)
        err_msg = "The project does not exist"
        assert err['status'] == 'failed', err_msg
        assert err['status_code'] == 404, err
        assert err['exception_cls'] == 'NotFound', err_msg
        assert err['target'] == 'project', err_msg

        # Get an empty task
        url = '/api/project/%s/newtask?offset=1000' % project.id
        res = self.app.get(url)
        assert res.data == '{}', res.data


    @patch('pybossa.repositories.project_repository.uploader')
    def test_project_delete_deletes_zip_files(self, uploader):
        """Test API project delete deletes also zip files of tasks and taskruns"""
        admin = UserFactory.create()
        project = ProjectFactory.create(owner=admin)
        task = TaskFactory.create(project=project)
        url = '/api/project/%s?api_key=%s' % (task.id, admin.api_key)
        res = self.app.delete(url)
        expected = [call('1_project1_task_json.zip', 'user_1'),
                    call('1_project1_task_csv.zip', 'user_1'),
                    call('1_project1_task_run_json.zip', 'user_1'),
                    call('1_project1_task_run_csv.zip', 'user_1')]
        assert uploader.delete_file.call_args_list == expected

    def test_project_post_with_reserved_fields_returns_error(self):
        user = UserFactory.create()
        CategoryFactory.create()
        data = dict(
            name='name',
            short_name='name',
            description='description',
            owner_id=user.id,
            long_description=u'Long Description\n================',
            info={},
            id=222,
            created='today',
            updated='now',
            contacted=False,
            completed=False)
        data = json.dumps(data)
        res = self.app.post('/api/project?api_key=' + user.api_key, data=data)

        assert res.status_code == 400, res.status_code
        error = json.loads(res.data)
        assert error['exception_msg'] == "Reserved keys in payload", error

    def test_project_put_with_reserved_returns_error(self):
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        url = '/api/project/%s?api_key=%s' % (project.id, user.api_key)
        data = {'created': 'today', 'updated': 'now',
                'contacted': False, 'completed': False,'id': 222}

        res = self.app.put(url, data=json.dumps(data))

        assert res.status_code == 400, res.status_code
        error = json.loads(res.data)
        assert error['exception_msg'] == "Reserved keys in payload", error
