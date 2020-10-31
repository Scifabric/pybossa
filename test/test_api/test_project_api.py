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
from mock import patch, call, MagicMock
from default import db, with_context
from nose.tools import assert_equal, assert_raises
from test_api import TestAPI

from factories import (ProjectFactory, TaskFactory, TaskRunFactory, AnonymousTaskRunFactory, UserFactory,
                       CategoryFactory, ExternalUidTaskRunFactory)

from pybossa.repositories import ProjectRepository
from pybossa.repositories import TaskRepository
from pybossa.repositories import ResultRepository
from pybossa.model.project import Project
project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
result_repo = ResultRepository(db)


class TestProjectAPI(TestAPI):

    def setUp(self):
        super(TestProjectAPI, self).setUp()
        db.session.query(Project).delete()

    def create_result(self, n_results=1, n_answers=1, owner=None,
                      filter_by=False):
        if owner:
            owner = owner
        else:
            owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        tasks = []
        for i in range(n_results):
            tasks.append(TaskFactory.create(n_answers=n_answers,
                                            project=project))
        for i in range(n_answers):
            for task in tasks:
                TaskRunFactory.create(task=task, project=project)
        if filter_by:
            return result_repo.filter_by(project_id=1)
        else:
            return result_repo.get_by(project_id=1)

    @with_context
    def test_project_query(self):
        """ Test API project query"""
        project1 = ProjectFactory.create(
            updated='2015-01-01T14:37:30.642119', info={'total': 150, 'task_presenter': 'foo'})
        projects = ProjectFactory.create_batch(
            8, info={'total': 150, 'task_presenter': 'foo'})

        project2 = ProjectFactory.create(
            updated='3019-01-01T14:37:30.642119', info={'total': 150, 'task_presenter': 'foo'})
        projects.insert(0, project1)
        projects.append(project2)
        res = self.app.get('/api/project')
        data = json.loads(res.data)
        dataNoDesc = data
        assert len(data) == 10, data
        project = data[0]
        assert project['info']['task_presenter'] == 'foo', data
        assert 'total' not in list(project['info'].keys()), data

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

        # Limits
        res = self.app.get("/api/project?limit=5")
        data = json.loads(res.data)
        assert len(data) == 5, data

        # Related
        res = self.app.get("/api/project?limit=1&related=True")
        data = json.loads(res.data)
        assert len(data) == 1, data
        keys = ['tasks', 'task_runs', 'results']
        for key in keys:
            assert key not in list(data[0].keys())

        # Stats
        res = self.app.get("/api/project?limit=1&stats=True")
        data = json.loads(res.data)
        assert len(data) == 1, data
        assert 'stats' in list(data[0].keys())
        assert data[0]['stats']['overall_progress'] == 0

        # Keyset pagination
        url = "/api/project?limit=5&last_id=%s" % (projects[4].id)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 5, len(data)
        assert data[0]['id'] == projects[5].id, (data[0]['id'], projects[5].id)

        # Desc filter
        url = "/api/project?orderby=updated&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        assert data[0]['updated'] == projects[len(
            projects)-1].updated, (err_msg, data)

        # Orderby filter
        url = "/api/project?orderby=id&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        assert data[0]['id'] == projects[len(projects)-1].id, err_msg

        # Orderby filter non attribute
        url = "/api/project?orderby=wrongattribute&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should return 415."
        assert data['status'] == 'failed', data
        assert data['status_code'] == 415, data
        assert 'has no attribute' in data['exception_msg'], data

        # Desc filter
        url = "/api/project?orderby=id"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        projects_by_id = sorted(projects, key=lambda x: x.id, reverse=False)
        for i in range(len(projects_by_id)):
            assert projects_by_id[i].id == data[i]['id'], (
                projects_by_id[i].id, data[i]['id'])

        url = "/api/project?orderby=id&desc=true"
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        projects_by_id = sorted(projects, key=lambda x: x.id, reverse=True)
        for i in range(len(projects_by_id)):
            assert projects_by_id[i].id == data[i]['id'], (
                projects_by_id[i].id, data[i]['id'])

    @with_context
    def test_project_query_with_context(self):
        """ Test API project query with context."""
        user = UserFactory.create()
        project_oc = ProjectFactory.create(owner=user, info={'total': 150})
        ProjectFactory.create()
        res = self.app.get('/api/project?api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, len(data)
        project = data[0]
        assert project['info']['total'] == 150, data
        assert project_oc.id == project['id'], project
        assert project['owner_id'] == user.id, project

        res = self.app.get('/api/project?api_key=' +
                           user.api_key + '&offset=1')
        data = json.loads(res.data)
        assert len(data) == 0, data

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # Test a non-existant ID
        res = self.app.get('/api/project/0?api_key=' + user.api_key)
        err = json.loads(res.data)
        assert res.status_code == 404, err
        assert err['status'] == 'failed', err
        assert err['target'] == 'project', err
        assert err['exception_cls'] == 'NotFound', err
        assert err['action'] == 'GET', err

        # Limits
        user_two = UserFactory.create()
        projects = ProjectFactory.create_batch(9, owner=user)
        res = self.app.get("/api/project?limit=5&api_key=" + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 5, data
        for d in data:
            d['owner_id'] == user.id, d

        res = self.app.get("/api/project?limit=5&api_key=" + user_two.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        res = self.app.get(
            "/api/project?all=1&limit=5&api_key=" + user_two.api_key)
        data = json.loads(res.data)
        assert len(data) == 5, data
        for d in data:
            d['owner_id'] == user.id, d

        # Keyset pagination
        url = "/api/project?limit=5&last_id=%s&api_key=%s" % (projects[3].id,
                                                              user.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 5, len(data)
        assert data[0]['id'] == projects[4].id, data
        for d in data:
            d['owner_id'] == user.id, d

        # Keyset pagination
        url = "/api/project?limit=5&last_id=%s&api_key=%s" % (projects[3].id,
                                                              user_two.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Keyset pagination
        url = "/api/project?all=1&limit=5&last_id=%s&api_key=%s" % (projects[3].id,
                                                                    user_two.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 5, data
        assert data[0]['id'] == projects[4].id, data
        for d in data:
            d['owner_id'] == user.id, d

    @with_context
    def test_query_project(self):
        """Test API query for project endpoint works"""
        ProjectFactory.create(short_name='test-app', name='My New Project')
        # Test for real field
        res = self.app.get("/api/project?short_name=test-app",
                           follow_redirects=True)
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
        res = self.app.get(
            '/api/project?short_name=test-app&name=My New Project')
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data
        assert data[0]['name'] == 'My New Project', data

    @with_context
    def test_query_project_with_context(self):
        """Test API query for project endpoint with context works"""
        user = UserFactory.create()
        user_two = UserFactory.create()
        project_oc = ProjectFactory.create(owner=user, short_name='test-app',
                                           name='My New Project',
                                           info=dict(foo='fox'))
        ProjectFactory.create()
        # Test for real field
        url = "/api/project?short_name=test-app&api_key=" + user.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data
        assert data[0]['owner_id'] == user.id, data[0]

        # Test for real field
        url = "/api/project?short_name=test-app&api_key=" + user_two.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        # Should return zero result
        assert len(data) == 0, data

        # Test for real field
        url = "/api/project?all=1&short_name=test-app&api_key=" + user_two.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data
        assert data[0]['owner_id'] == user.id, data[0]

        # Valid field but wrong value
        url = "/api/project?short_name=wrongvalue&api_key=" + user.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        url = '/api/project?short_name=test-app&name=My New Project&api_key=' + user.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data
        assert data[0]['name'] == 'My New Project', data
        assert data[0]['owner_id'] == user.id, data

        # Multiple fields
        url = '/api/project?short_name=test-app&name=My New Project&api_key=' + user_two.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        # Zero result
        assert len(data) == 0, data

        # Multiple fields
        url = '/api/project?all=1&short_name=test-app&name=My New Project&api_key=' + user_two.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        # One result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data
        assert data[0]['name'] == 'My New Project', data
        assert data[0]['owner_id'] == user.id, data

        # fulltextsearch
        url = '/api/project?&info=foo::fox&fulltextsearch=1'
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 1, len(data)

    @with_context
    def test_project_post(self):
        """Test API project creation and auth"""
        users = UserFactory.create_batch(2)
        cat1 = CategoryFactory.create()
        cat2 = CategoryFactory.create()
        name = 'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project',
            description='description',
            owner_id=1,
            long_description='Long Description\n================')
        data = json.dumps(data)
        # no api-key
        res = self.app.post('/api/project', data=data)
        assert_equal(res.status, '401 UNAUTHORIZED',
                     'Should not be allowed to create')

        assert res.mimetype == 'application/json'
        # now a real user
        res = self.app.post('/api/project?api_key=' + users[1].api_key,
                            data=data)
        out = project_repo.get_by(name=name)
        assert out, out
        assert_equal(out.short_name, 'xxxx-project'), out
        assert_equal(out.owner.name, 'user2')
        assert_equal(out.owners_ids, [2])
        id_ = out.id

        # now a real user with headers auth
        headers = [('Authorization', users[1].api_key)]
        new_project = dict(
            name=name + '2',
            short_name='xxxx-project2',
            description='description2',
            owner_id=1,
            long_description='Long Description\n================')
        new_project = json.dumps(new_project)
        res = self.app.post('/api/project', headers=headers,
                            data=new_project)
        out = project_repo.get_by(name=name + '2')
        assert out, out
        assert_equal(out.short_name, 'xxxx-project2'), out
        assert_equal(out.owner.name, 'user2')
        # Test that a default category is assigned to the project
        assert cat1.id == out.category_id, "No category assigned to project"
        id_ = out.id

        # now a real user with headers auth and specific category_id
        headers = [('Authorization', users[1].api_key)]
        new_project2 = dict(
            name=name + '3',
            short_name='xxxx-project3',
            description='description3',
            owner_id=1,
            category_id=cat2.id,
            long_description='Long Description\n================')
        new_project2 = json.dumps(new_project2)
        res = self.app.post('/api/project', headers=headers,
                            data=new_project2)
        out = project_repo.get_by(name=name + '3')
        assert out, out
        assert_equal(out.short_name, 'xxxx-project3'), out
        assert_equal(out.owner.name, 'user2')
        # Test that a default category is assigned to the project
        assert cat2.id == out.category_id, "No category assigned to project"

        # now a real user with headers auth and non-existing category_id
        headers = [('Authorization', users[1].api_key)]
        new_project3 = dict(
            name=name + '4',
            short_name='xxxx-project4',
            description='description4',
            owner_id=1,
            category_id=5014,
            long_description='Long Description\n================')
        new_project3 = json.dumps(new_project3)
        res = self.app.post('/api/project', headers=headers,
                            data=new_project3)
        err = json.loads(res.data)
        assert err['status'] == 'failed'
        assert err['exception_msg'] == 'category_id does not exist'
        assert err['status_code'] == 400

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
        data = dict(name='My New Title', links='hateoas', info={})
        datajson = json.dumps(data)
        # anonymous
        res = self.app.put('/api/project/%s' % id_, data=datajson)
        error_msg = 'Anonymous should not be allowed to update'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'PUT', error
        assert error['exception_cls'] == 'Unauthorized', error

        # real user but not allowed as not owner!
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
        assert 'task_presenter' not in list(out.get('info').keys()), error

        data['info']['task_presenter'] = 'htmlpresenter'
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
        datajson = {'foo': 'bar'}
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
            long_description='Long Description\n================')

        datajson = json.dumps(data)
        res = self.app.put('/api/project/%s?api_key=%s&search=select1' % (id_, users[1].api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

        # test delete
        # anonymous
        res = self.app.delete('/api/project/%s' % id_, data=data)
        error_msg = 'Anonymous should not be allowed to delete'
        assert_equal(res.status, '401 UNAUTHORIZED', error_msg)
        error = json.loads(res.data)
        assert error['status'] == 'failed', error
        assert error['action'] == 'DELETE', error
        assert error['target'] == 'project', error
        # real user but not allowed as not owner!
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
        assert res.mimetype == 'application/json'

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
        name = 'XXXX Project'
        data = dict(
            name=name,
            short_name='new',
            description='description',
            owner_id=1,
            long_description='Long Description\n================')
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
        name = 'XXXX Project'
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
        # admin user but not owner!
        url = '/api/project/%s?api_key=%s' % (project.id, admin.api_key)
        res = self.app.put(url, data=datajson, follow_redirects=True)

        assert_equal(res.status, '200 OK', res.data)
        out2 = project_repo.get(project.id)
        assert_equal(out2.name, data['name'])
        assert res.mimetype == 'application/json'

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

        # DELETE success real user  not owner!
        res = self.app.delete(url, data=json.dumps(data))
        assert_equal(res.status, '204 NO CONTENT', res.data)
        assert res.mimetype == 'application/json'

    @with_context
    def test_user_progress_anonymous(self):
        """Test API userprogress as anonymous works"""
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        tasks = TaskFactory.create_batch(2, project=project)
        taskruns = []
        for task in tasks:
            taskruns.extend(AnonymousTaskRunFactory.create_batch(2, task=task))

        res = self.app.get('/api/project/1/userprogress',
                           follow_redirects=True)
        data = json.loads(res.data)
        print(data)

        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "The reported number of done tasks is wrong"
        assert len(taskruns) == data['done'], data

        # Add a new TaskRun and check again
        taskrun = AnonymousTaskRunFactory.create(
            task=tasks[0], info={'answer': 'hello'})

        res = self.app.get('/api/project/1/userprogress',
                           follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "Number of done tasks is wrong: %s" % len(taskruns)
        assert len(taskruns) + 1 == data['done'], error_msg

    @with_context
    def test_external_user_id_progress_anonymous(self):
        """Test API userprogress as external_uid works"""
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        tasks = TaskFactory.create_batch(5, project=project)
        taskruns = []
        taskruns_external_2 = []
        for task in tasks:
            taskruns.extend(
                ExternalUidTaskRunFactory.create_batch(2, task=task))

        for task in tasks:
            taskruns_external_2.extend(
                ExternalUidTaskRunFactory.create_batch(5, task=task, external_uid='test@token.com'))

        res = self.app.get('/api/project/1/userprogress?external_uid=1xa',
                           follow_redirects=True)
        data = json.loads(res.data)

        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        res = self.app.get('/api/project/1/userprogress?external_uid=test@token.com',
                           follow_redirects=True)
        data_external_uid_2 = json.loads(res.data)

        error_msg = "The reported total number of tasks is wrong"
        assert data['total'] == len(tasks), error_msg

        error_msg = "The reported number of task runs is wrong"
        assert len(taskruns) == data['done'], data

        assert len(taskruns_external_2) == data_external_uid_2['done'], data

        # Add a new TaskRun and check again
        taskrun = ExternalUidTaskRunFactory.create(
            task=tasks[0], info={'answer': 'hello'})

        res = self.app.get('/api/project/1/userprogress?external_uid=1xa',
                           follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "Number of done tasks is wrong: %s" % len(taskruns)
        assert len(taskruns) + 1 == data['done'], error_msg

    @ with_context
    def test_user_progress_authenticated_user(self):
        """Test API userprogress as an authenticated user works"""
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        tasks = TaskFactory.create_batch(2, project=project)
        taskruns = []
        for task in tasks:
            taskruns.extend(TaskRunFactory.create_batch(
                2, task=task, user=user))

        url = '/api/project/1/userprogress?api_key=%s' % user.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        url = '/api/project/%s/userprogress?api_key=%s' % (
            project.short_name, user.api_key)
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
        taskrun = TaskRunFactory.create(
            task=tasks[0], info={'answer': 'hello'}, user=user)

        url = '/api/project/1/userprogress?api_key=%s' % user.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "The reported total number of tasks is wrong"
        assert len(tasks) == data['total'], error_msg

        error_msg = "Number of done tasks is wrong: %s" % len(taskruns)
        assert len(taskruns) + 1 == data['done'], error_msg

    @ with_context
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

    @ with_context
    def test_newtask_allow_anonymous_contributors(self):
        """Test API get a newtask - allow anonymous contributors"""
        project = ProjectFactory.create()
        user = UserFactory.create()
        tasks = TaskFactory.create_batch(
            2, project=project, info={'question': 'answer'})

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

    @ with_context
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
        assert res.data == b'{}', res.data

    @ with_context
    @ patch('pybossa.repositories.project_repository.uploader')
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

    @ with_context
    def test_project_post_with_reserved_fields_returns_error(self):
        user = UserFactory.create()
        CategoryFactory.create()
        data = dict(
            name='name',
            short_name='name',
            description='description',
            owner_id=user.id,
            long_description='Long Description\n================',
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

    @ with_context
    def test_project_put_with_reserved_returns_error(self):
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        url = '/api/project/%s?api_key=%s' % (project.id, user.api_key)
        data = {'created': 'today', 'updated': 'now',
                'contacted': False, 'completed': False, 'id': 222}

        res = self.app.put(url, data=json.dumps(data))

        assert res.status_code == 400, res.status_code
        error = json.loads(res.data)
        assert error['exception_msg'] == "Reserved keys in payload", error

    @ with_context
    def test_project_post_with_published_attribute_is_forbidden(self):
        user = UserFactory.create()
        data = dict(
            name='name',
            short_name='name',
            description='description',
            owner_id=user.id,
            long_description='Long Description\n================',
            info={'task_presenter': '<div>'},
            published=True)
        data = json.dumps(data)

        res = self.app.post('/api/project?api_key=' + user.api_key, data=data)

        error_msg = json.loads(res.data)['exception_msg']
        assert res.status_code == 403, res.status_code
        assert error_msg == 'You cannot publish a project via the API', res.data

    @ with_context
    def test_project_update_with_published_attribute_is_forbidden(self):
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        data = dict(published=True)
        data = json.dumps(data)
        url = '/api/project/%s?api_key=%s' % (project.id, user.api_key)

        res = self.app.put(url, data=data)
        print((res.data))
        error_msg = json.loads(res.data)['exception_msg']
        assert res.status_code == 403, res.status_code
        assert error_msg == 'You cannot publish a project via the API', res.data

    @ with_context
    def test_project_delete_with_results(self):
        """Test API delete project with results cannot be deleted."""
        result = self.create_result()
        project = project_repo.get(result.project_id)
        url = '/api/project/%s?api_key=%s' % (result.project_id,
                                              project.owner.api_key)

        res = self.app.delete(url)
        assert_equal(res.status, '403 FORBIDDEN', res.status)

    @ with_context
    def test_project_delete_with_results_var(self):
        """Test API delete project with results cannot be deleted by admin."""
        root = UserFactory.create(admin=True)
        result = self.create_result()
        project = project_repo.get(result.project_id)

        url = '/api/project/%s?api_key=%s' % (result.project_id,
                                              root.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '403 FORBIDDEN', res.status)

    @ with_context
    @ patch('pybossa.api.api_base.caching')
    def test_project_cache_post_is_refreshed(self, caching_mock):
        """Test API project cache is updated after POST."""
        clean_project_mock = MagicMock()
        caching_mock.get.return_value = dict(refresh=clean_project_mock)
        owner = UserFactory.create()
        category = CategoryFactory.create()
        url = '/api/project?api_key=%s' % owner.api_key
        payload = dict(name='foo', short_name='foo', description='foo')
        res = self.app.post(url, data=json.dumps(payload))
        print((res.data))
        project_id = json.loads(res.data)['id']
        clean_project_mock.assert_called_with(project_id), res.data

    @ with_context
    @ patch('pybossa.api.api_base.caching')
    def test_project_cache_put_is_refreshed(self, caching_mock):
        """Test API project cache is updated after PUT."""
        clean_project_mock = MagicMock()
        caching_mock.get.return_value = dict(refresh=clean_project_mock)
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        url = '/api/project/%s?api_key=%s' % (project.id, owner.api_key)
        payload = project.dictize()
        payload['info'] = {'foo': 'bar'}
        del payload['id']
        del payload['created']
        del payload['updated']
        del payload['contacted']
        del payload['published']
        del payload['owner_id']
        del payload['secret_key']
        res = self.app.put(url, data=json.dumps(payload))
        clean_project_mock.assert_called_with(project.id)

    @ with_context
    @ patch('pybossa.api.api_base.caching')
    def test_project_cache_delete_is_refreshed(self, caching_mock):
        """Test API project cache is updated after DEL."""
        clean_project_mock = MagicMock()
        caching_mock.get.return_value = dict(refresh=clean_project_mock)
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        url = '/api/project/%s?api_key=%s' % (project.id, owner.api_key)
        res = self.app.delete(url)
        clean_project_mock.assert_called_with(project.id)

    @ with_context
    def test_project_filter_by_category_works(self):
        """Test API project filter by category works."""
        category = CategoryFactory.create()
        projects_published = ProjectFactory.create_batch(2,
                                                         published=True,
                                                         category=category)
        projects_not_published = ProjectFactory.create_batch(2,
                                                             published=False,
                                                             category=category)
        res = self.app.get('/api/project?category_id=%s' % category.id)
        data = json.loads(res.data)
        assert len(data) == 2, data
        assert data[0]['id'] == projects_published[0].id
        assert data[1]['id'] == projects_published[1].id
