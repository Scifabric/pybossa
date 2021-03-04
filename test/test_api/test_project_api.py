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
from default import db, with_context, with_context_settings, flask_app
from nose.tools import assert_equal, assert_raises
import copy
from test_api import TestAPI
from helper.gig_helper import make_subadmin, make_admin

from factories import (ProjectFactory, TaskFactory, TaskRunFactory, AnonymousTaskRunFactory, UserFactory,
                       CategoryFactory, AuditlogFactory)

from pybossa.core import signer
from pybossa.repositories import ProjectRepository
from pybossa.repositories import TaskRepository
from pybossa.repositories import ResultRepository
from pybossa.model.project import Project


project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)
result_repo = ResultRepository(db)


class TestProjectAPI(TestAPI):

    patch_data_access_levels = dict(
        valid_access_levels=[("L1", "L1"), ("L2", "L2"),("L3", "L3"), ("L4", "L4")],
        valid_user_levels_for_project_level=dict(
            L1=[], L2=["L1"], L3=["L1", "L2"], L4=["L1", "L2", "L3"]),
        valid_project_levels_for_user_level=dict(
            L1=["L2", "L3", "L4"], L2=["L3", "L4"], L3=["L4"], L4=[]),
        valid_user_access_levels=[("L1", "L1"), ("L2", "L2"),("L3", "L3"), ("L4", "L4")]
    )

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
            updated='2015-01-01T14:37:30.642119',
            info={
                'total': 150,
                'task_presenter': 'foo',
                'data_classification': dict(input_data="L4 - public", output_data="L4 - public")
            })
        projects = ProjectFactory.create_batch(8,
            info={
                'total': 150,
                'task_presenter': 'foo',
                'data_classification': dict(input_data="L4 - public", output_data="L4 - public")
            })

        project2 = ProjectFactory.create(
            updated='2022-01-01T14:37:30.642119',
            info={
                'total': 150,
                'task_presenter': 'foo',
                'data_classification': dict(input_data="L4 - public", output_data="L4 - public")
            })
        user = UserFactory.create()

        projects.insert(0, project1)
        projects.append(project2)
        res = self.app.get('/api/project')
        data = json.loads(res.data)
        assert data['status_code'] == 401, "anonymous user should not have acess to project api"

        res = self.app.get('/api/project?&all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        project = data[0]
        err_msg = 'Task presenter should not be returned for regular user'
        assert 'task_presenter' not in project['info'], err_msg

        admin = UserFactory.create(admin=True)
        res = self.app.get('/api/project?all=1&api_key=' + admin.api_key)
        data = json.loads(res.data)
        dataNoDesc = data
        assert len(data) == 10, data
        project = data[0]
        assert project['info']['task_presenter'] == 'foo', data

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
        res = self.app.get('/api/project?all=1&limit=5&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 5, data

        # Related
        res = self.app.get('/api/project?all=1&limit=1&related=True&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, data
        keys = ['tasks', 'task_runs', 'results']
        for key in keys:
            assert key not in data[0].keys()

        # Stats
        res = self.app.get("/api/project?limit=1&all=1&stats=True&api_key=" + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, data
        assert 'stats' in data[0].keys()
        assert data[0]['stats']['overall_progress'] == 0

        # Keyset pagination
        url = "/api/project?all=1&limit=5&last_id=%s&api_key=%s" % (projects[4].id, user.api_key)
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 5, len(data)
        assert data[0]['id'] == projects[5].id, (data[0]['id'], projects[5].id)

        # Desc filter
        url = '/api/project?all=1&orderby=updated&desc=true&api_key=' + user.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        assert data[0]['updated'] == projects[len(projects)-1].updated, err_msg

        # Orderby filter
        url = '/api/project?all=1&orderby=id&desc=true&api_key=' + user.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        assert data[0]['id'] == projects[len(projects)-1].id, err_msg

        # Orderby filter non attribute
        url = '/api/project?all=1&orderby=wrongattribute&desc=true&api_key=' + user.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should return 415."
        assert data['status'] == 'failed', data
        assert data['status_code'] == 415, data
        assert 'has no attribute' in data['exception_msg'], data

        # Desc filter
        url = '/api/project?all=1&orderby=id&api_key=' + user.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        projects_by_id = sorted(projects, key=lambda x: x.id, reverse=False)
        for i in range(len(projects_by_id)):
            assert projects_by_id[i].id == data[i]['id'], (projects_by_id[i].id, data[i]['id'])

        url = '/api/project?all=1&orderby=id&desc=true&api_key=' + user.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        err_msg = "It should get the last item first."
        projects_by_id = sorted(projects, key=lambda x: x.id, reverse=True)
        for i in range(len(projects_by_id)):
            assert projects_by_id[i].id == data[i]['id'], (projects_by_id[i].id, data[i]['id'])

    @with_context
    def test_project_query_with_context(self):
        """ Test API project query with context."""
        user = UserFactory.create()
        project_oc = ProjectFactory.create(
            owner=user,
            info={
                'total': 150,
                'data_classification': dict(input_data="L4 - public", output_data="L4 - public")
            })
        ProjectFactory.create()
        res = self.app.get('/api/project?api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 1, len(data)
        project = data[0]
        assert project['info']['total'] == 150, data
        assert project_oc.id == project['id'], project
        assert project['owner_id'] == user.id, project

        res = self.app.get('/api/project?api_key=' + user.api_key + '&offset=1')
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

        res = self.app.get("/api/project?all=1&limit=5&api_key=" + user_two.api_key)
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
        user = UserFactory.create()
        # Test for real field
        res = self.app.get('/api/project?short_name=test-app&all=1&api_key=' + user.api_key, follow_redirects=True)
        data = json.loads(res.data)
        # Should return one result
        assert len(data) == 1, data
        # Correct result
        assert data[0]['short_name'] == 'test-app', data

        # Valid field but wrong value
        res = self.app.get('/api/project?short_name=wrongvalue&all=1&api_key=' + user.api_key)
        data = json.loads(res.data)
        assert len(data) == 0, data

        # Multiple fields
        res = self.app.get('/api/project?short_name=test-app&name=My New Project&all=1&api_key=' + user.api_key)
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
                                           info=dict(
                                               foo='fox',
                                               data_classification=dict(input_data="L4 - public", output_data="L4 - public")
                                            ))
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
        url = '/api/project?&info=foo::fox&fulltextsearch=1&all=1&api_key=' + user_two.api_key
        res = self.app.get(url)
        data = json.loads(res.data)
        assert len(data) == 1, len(data)

    @with_context
    def test_project_post(self):
        """Test API project creation and auth"""
        users = UserFactory.create_batch(2)
        make_subadmin(users[1])
        cat1 = CategoryFactory.create()
        cat2 = CategoryFactory.create()
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project',
            description='description',
            owner_id=1,
            long_description=u'Long Description\n================',
            password="hello",
            info=dict(
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=0.5,
                product="abc",
                subproduct="def",
            ))
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
            long_description=u'Long Description\n================',
            password="hello",
            info=dict(
                task_presenter='taskpresenter',
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=0.5,
                product="abc",
                subproduct="def",
            ))
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
            long_description=u'Long Description\n================',
            password="hello",
            info=dict(
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=0.5,
                product="abc",
                subproduct="def",
            ))
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
            long_description=u'Long Description\n================',
            password="hello",
            info=dict(
                task_presenter='taskpresenter',
                data_classification=dict(input_data="L1 - internal", output_data="L4 - public"),
                kpi=0.5,
                product="abc",
                subproduct="def",
            ))
        new_project3 = json.dumps(new_project3)
        res = self.app.post('/api/project', headers=headers,
                            data=new_project3)
        err = json.loads(res.data)
        assert err['status'] == 'failed', res.data
        assert err['exception_msg'] == 'category_id does not exist', res.data
        assert err['status_code'] == 400, res.data

        # test re-create should fail
        res = self.app.post('/api/project?api_key=' + users[1].api_key,
                            data=data)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == "DBIntegrityError", err

        # test create with non-allowed fields should fail
        data = dict(name='fail', short_name='fail', description="test", link='hateoas', password="hello", wrong=15)
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
        data = dict(
            name='My New Title',
            links='hateoas',
            info=dict(data_classification=dict(input_data="L4 - public", output_data="L4 - public"), kpi=0.5)
        )
        datajson = json.dumps(data)
        ## anonymous
        res = self.app.put('/api/project/%s' % id_, data=datajson)
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
        data['info'] = {}
        newdata = json.dumps(data)
        res = self.app.put('/api/project/%s?api_key=%s' % (id_, users[1].api_key),
                           data=newdata)

        assert_equal(res.status, '200 OK', res.data)
        out2 = project_repo.get(id_)
        assert_equal(out2.name, data['name'])
        out = json.loads(res.data)
        assert out.get('status') is None, error
        assert out.get('id') == id_, error
        out_info = out.get('info')
        assert out_info is not None, error
        # assert out_info.get('task_presenter') is None, error

        # Subadmin can update task presenter when DISABLE_EDITOR = False
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
        assert res.status_code == 403, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'Forbidden', err

        empty_data = dict(
            name=name,
            short_name='',
            description='',
            owner_id=1,
            long_description=u'Long Description\n================',
            password="hello",
            info=dict(
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=0.5
            ))
        empty_data = json.dumps(empty_data)

        res = self.app.post('/api/project?api_key=' + users[1].api_key,
                            data=empty_data)
        err = json.loads(res.data)

        assert res.status_code == 400, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'POST', err
        assert err['exception_cls'] == 'BadRequest', err

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
            long_description=u'Long Description\n================',
            password="hello")

        datajson = json.dumps(data)
        res = self.app.put('/api/project/%s?api_key=%s&search=select1' % (id_, users[1].api_key),
                           data=datajson)
        err = json.loads(res.data)
        assert res.status_code == 415, err
        assert err['status'] == 'failed', err
        assert err['action'] == 'PUT', err
        assert err['exception_cls'] == 'AttributeError', err

    @with_context
    def test_delete(self):
        """Test API project deletion and auth"""
        users = UserFactory.create_batch(2)
        make_subadmin(users[1])
        non_owner = UserFactory.create()
        cat1 = CategoryFactory.create()
        
        # create project
        headers = [('Authorization', users[1].api_key)]
        name='project'
        new_project = dict(
            name=name,
            short_name='project',
            description='description',
            owner_id=1,
            long_description='Long Description',
            password="hello",
            info=dict(
                task_presenter='taskpresenter',
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=0.5,
                product="abc",
                subproduct="def"
            ))

        res = self.app.post('/api/project', headers=headers,
                            data=json.dumps(new_project))
        out = project_repo.get_by(name=name)
        id_ = out.id

        # test delete
        data = dict(
            name=name,
            short_name='project',
            long_description=u'Long Description',
            password="hello")

        datajson = json.dumps(data)
        ## anonymous
        res = self.app.delete('/api/project/%s' % id_, data=datajson)
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
        assert res.mimetype == 'application/json'

        # delete a project that does not exist
        url = '/api/project/%s?api_key=%s' % (5000, users[1].api_key)
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
    @patch('pybossa.model.project.signer')
    def test_project_update_task_presenter(self, hasher_mock):
        """Test API project task presenter on PUT and POST"""
        from flask import current_app
        from pybossa.core import setup_task_presenter_editor

        current_app.config['DISABLE_TASK_PRESENTER_EDITOR'] = True
        setup_task_presenter_editor(current_app)

        [admin, subadmin] = UserFactory.create_batch(2)
        make_admin(admin)
        make_subadmin(subadmin)
        CategoryFactory.create()

        hasher_mock.generate_password_hash.return_value = "hashedpwd"

        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project',
            description='description',
            owner_id=subadmin.id,
            long_description=u'Long Description\n================',
            password="hello",
            info=dict(
                task_presenter='taskpresenter',
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=0.5,
                product="abc",
                subproduct="def",
            ))
        newdata = json.dumps(data)

        # Subadmin cannot create project with task presenter
        res = self.app.post('/api/project?api_key=' + subadmin.api_key,
                            data=newdata)

        assert_equal(res.status, '401 UNAUTHORIZED', res.data)
        out = json.loads(res.data)
        assert out.get('status') == 'failed', res.data

        # Subadmin can create project without task presenter
        data['info'].pop('task_presenter')
        newdata = json.dumps(data)
        res = self.app.post('/api/project?api_key=' + subadmin.api_key,
                            data=newdata)

        out = project_repo.get_by(name=name)
        assert out, out
        assert_equal(out.short_name, u'xxxx-project'), out
        assert_equal(out.owner.name, u'user2')
        assert_equal(out.owners_ids, [subadmin.id])
        assert_equal(out.info, {
            u'data_classification': {u'input_data': u'L4 - public', u'output_data': u'L4 - public'}, 
            u'data_access': [u'L4'], 
            u'passwd_hash': u'hashedpwd', 
            u'kpi': 0.5,
            u'product': u'abc',
            u'subproduct': u'def',
            })
        id_ = out.id

        # Subadmin cannot update project task presenter
        data = dict(info=dict(task_presenter='taskpresenter'))
        newdata = json.dumps(data)
        res = self.app.put(
            '/api/project/{}?api_key={}'.format(id_, subadmin.api_key),
            data=newdata)

        assert_equal(res.status, '401 UNAUTHORIZED', res.data)
        out = json.loads(res.data)
        assert out.get('status') == 'failed', res.data

        # Admin can create project with task presenter
        name=u'XXXX Project 2'
        data = dict(
            name=name,
            short_name=u'xxxx-project-2',
            description=u'description',
            owner_id=admin.id,
            long_description=u'Long Description\n================',
            password=u'hello',
            info=dict(
                task_presenter=u'taskpresenter',
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=0.5,
                product="abc",
                subproduct="def",
            ))

        newdata = json.dumps(data)
        res = self.app.post('/api/project?api_key=' + admin.api_key,
                            data=newdata)
        out = project_repo.get_by(name=name)
        assert out, out
        assert_equal(out.short_name, u'xxxx-project-2'), out
        assert_equal(out.owner.name, u'user1')
        assert_equal(out.owners_ids, [1])
        assert_equal(out.info, {
            u'kpi': 0.5, 
            u'task_presenter': u'taskpresenter', 
            u'passwd_hash': u'hashedpwd', 
            u'data_classification': {u'input_data': u'L4 - public', u'output_data': u'L4 - public'}, 
            u'data_access': [u'L4'],
            u'product': u'abc',
            u'subproduct': u'def',
            })
        id_ = out.id

         # Admin can update project task presenter
        data = dict(info=dict(task_presenter='new-taskpresenter'))
        newdata = json.dumps(data)
        res = self.app.put(
            '/api/project/{}?api_key={}'.format(id_, admin.api_key),
            data=newdata)

        out = project_repo.get_by(name=name)
        assert out, out
        assert_equal(out.short_name, 'xxxx-project-2'), out
        assert_equal(out.owner.name, 'user1')
        assert_equal(out.owners_ids, [1])
        assert_equal(out.info, {
            u'kpi': 0.5, 
            u'task_presenter': u'new-taskpresenter', 
            u'data_classification': {u'input_data': u'L4 - public', u'output_data': u'L4 - public'}, 
            u'data_access': [u'L4'], 
            u'passwd_hash': u'hashedpwd',
            u'product': u'abc',
            u'subproduct': u'def',
            })
        assert out.id == id_, out

    @with_context
    def test_project_post_invalid_short_name(self):
        """Test API project POST returns error if short_name is invalid (i.e. is
            a name used by the Flask app as a URL endpoint"""
        users = UserFactory.create_batch(2, subadmin=True)
        CategoryFactory.create()
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='new',
            description='description',
            owner_id=1,
            password="hello",
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

        ### DELETE success real user  not owner!
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

        res = self.app.get('/api/project/1/userprogress', follow_redirects=True)
        data = json.loads(res.data)
        assert res.status_code == 401, res.data
        return

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

        assert 'remaining' in data
        assert 'remaining_for_user' in data

    @with_context
    def test_user_progress_n_gold_tasks(self):
        """Test API userprogress as an authenticated user works"""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        tasks = TaskFactory.create_batch(2, project=project)
        tasks = TaskFactory.create_batch(2, project=project, calibration = 1)
        taskruns = []
        for task in tasks:
            taskruns.extend(TaskRunFactory.create_batch(2, task=task, user=user))

        url = '/api/project/1/userprogress?api_key=%s' % user.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        assert 'available_gold_tasks' not in data, data

        # non-subadmin owner
        url = '/api/project/1/userprogress?api_key=%s' % owner.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        assert 'available_gold_tasks' not in data, data

        # subadmin owner
        owner.subadmin = True
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        assert 'available_gold_tasks' in data, data
        assert data['available_gold_tasks'] == 2

        url = '/api/project/1/userprogress?api_key=%s' % admin.api_key
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        assert 'available_gold_tasks' in data, data
        assert data['available_gold_tasks'] == 2

    @with_context
    def test_user_progress_guidelines_updated(self):
        """Test API userprogress as an authenticated user works"""

        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        tasks = TaskFactory.create_batch(2, project=project)
        url = '/api/project/%s/userprogress?api_key=%s' % (project.id, owner.api_key)
        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        assert data['guidelines_updated'] is False, data

        TaskRunFactory.create(task=tasks[0], project=project, user=owner)

        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        assert data['guidelines_updated'] is False, data

        AuditlogFactory.create_batch(size=3, project_id=project.id,
            project_short_name=project.short_name,
            user_id=project.owner.id,
            user_name=project.owner.name,
            attribute='task_guidelines',
            old_value="old_task_guidelines1",
            new_value="new_task_guidelines2")

        res = self.app.get(url, follow_redirects=True)
        data = json.loads(res.data)
        assert data['guidelines_updated'] is True, data


    @with_context
    def test_task_progress_anonymous(self):
        """Test API taskprogress as anonymous works"""
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        tasks = TaskFactory.create_batch(2, project=project)
        taskruns = []
        for task in tasks:
            taskruns.extend(AnonymousTaskRunFactory.create_batch(2, task=task))

        # check basic query without constraints to filter tasks  
        res = self.app.get('/api/project/1/taskprogress', follow_redirects=True)
        data = json.loads(res.data)
        assert res.status_code == 200, res.data

        # check 404 response when the project doesn't exist   
        res = self.app.get('/api/project//taskprogress', follow_redirects=True)
        data = json.loads(res.data)
        error_msg = "A valid project must be used"
        assert res.status_code == 404, error_msg


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
    @patch('pybossa.api.pwd_manager.ProjectPasswdManager.password_needed')
    def test_newtask_allow_anonymous_contributors(self, passwd_needed):
        """Test API get a newtask - do not allow anonymous contributors"""
        project = ProjectFactory.create()
        user = UserFactory.create()
        tasks = TaskFactory.create_batch(2, project=project, info={'question': 'answer'})
        passwd_needed.return_value = False

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
        assert 'error' in task['info'], 'No anonymous contributors'

        # The output should have a mime-type: application/json
        assert res.mimetype == 'application/json', res

        # as a real user
        self.set_proj_passwd_cookie(project, user)
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
        url = '/api/project/%s/newtask?offset=1000&api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url)
        assert res.data == '{}', res.data

    @with_context
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

    @with_context
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

    @with_context
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

    @with_context
    def test_project_post_with_published_attribute_requires_password(self):
        user = UserFactory.create()
        data = dict(
            name='name',
            short_name='name',
            description='description',
            owner_id=user.id,
            long_description=u'Long Description\n================',
            info={'task_presenter': '<div>'},
            published=True)
        data = json.dumps(data)

        res = self.app.post('/api/project?api_key=' + user.api_key, data=data)

        error_msg = json.loads(res.data)['exception_msg']
        assert res.status_code == 400, res.status_code
        assert error_msg == 'password required', res.data

    @with_context
    def test_project_post_without_desc_and_long_desc_raise_error(self):
        user = UserFactory.create()
        data = dict(
            name='name',
            short_name='name',
            owner_id=user.id,
            info={'task_presenter': '<div>'},
            published=True)
        data = json.dumps(data)

        res = self.app.post('/api/project?api_key=' + user.api_key, data=data)

        error_msg = json.loads(res.data)['exception_msg']
        assert res.status_code == 400, res.status_code
        assert error_msg == 'description or long description required', res.data

    @with_context
    def test_project_update_with_published_attribute_is_not_forbidden(self):
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        data = dict(published=True)
        data = json.dumps(data)
        url = '/api/project/%s?api_key=%s' % (project.id, user.api_key)

        res = self.app.put(url, data=data)
        assert res.status_code == 200, res.status_code

    @with_context
    def test_project_delete_with_results(self):
        """Test API delete project with results can be deleted."""
        result = self.create_result()
        project = project_repo.get(result.project_id)
        url = '/api/project/%s?api_key=%s' % (result.project_id,
                                              project.owner.api_key)

        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.status)

    @with_context
    def test_project_delete_with_results_var(self):
        """Test API delete project with results can be deleted by admin."""
        root = UserFactory.create(admin=True)
        result = self.create_result()
        project = project_repo.get(result.project_id)

        url = '/api/project/%s?api_key=%s' % (result.project_id,
                                              root.api_key)
        res = self.app.delete(url)
        assert_equal(res.status, '204 NO CONTENT', res.status)

    @with_context
    @patch('pybossa.api.api_base.caching')
    def test_project_cache_post_is_refreshed(self, caching_mock):
        """Test API project cache is updated after POST."""
        clean_project_mock = MagicMock()
        caching_mock.get.return_value = dict(refresh=clean_project_mock)
        owner = UserFactory.create()
        category = CategoryFactory.create()
        url = '/api/project?api_key=%s' % owner.api_key
        payload = dict(name='foo', short_name='foo', description='foo', password="hey",
                       info=dict(
                           data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                           kpi=0.5,
                           product="abc",
                           subproduct="def",
                        ))
        res = self.app.post(url, data=json.dumps(payload))
        project_id = json.loads(res.data)['id']
        clean_project_mock.assert_called_with(project_id), res.data


    @with_context
    @patch('pybossa.api.api_base.caching')
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

    @with_context
    @patch('pybossa.api.api_base.caching')
    def test_project_cache_delete_is_refreshed(self, caching_mock):
        """Test API project cache is updated after DEL."""
        clean_project_mock = MagicMock()
        caching_mock.get.return_value = dict(refresh=clean_project_mock)
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        url = '/api/project/%s?api_key=%s' % (project.id, owner.api_key)
        res = self.app.delete(url)
        clean_project_mock.assert_called_with(project.id)

    @with_context
    def put_project_does_not_change_password(self):
        """Test password is not changed after PUT."""
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        project.set_password('hello_world')
        project_repo.save(project)
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
        project = project_repo.get(project.id)
        assert project.check_password('hello_world')

    @with_context
    def put_project_does_not_remove_password(self):
        """Test password is not removed after PUT."""
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        project.set_password('hello_world')
        project_repo.save(project)
        url = '/api/project/%s?api_key=%s' % (project.id, owner.api_key)
        payload = project.dictize()
        payload['info'] = {'foo': 'bar', 'passwd_hash': None}
        del payload['id']
        del payload['created']
        del payload['updated']
        del payload['contacted']
        del payload['published']
        del payload['owner_id']
        del payload['secret_key']
        res = self.app.put(url, data=json.dumps(payload))
        project = project_repo.get(project.id)
        assert project.check_password('hello_world')

    @with_context
    def put_project_updates_info(self):
        """Test info is merged after PUT."""
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        old_info = project.info
        project_repo.save(project)
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
        project = project_repo.get(project.id)

        for key, value in old_info.iteritems():
            if not payload['info'].get(key):
                assert project.info.get(key) == value

    @with_context
    def put_project_does_not_remove_info(self):
        """Test info is not removed after PUT."""
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        old_info = project.info
        project_repo.save(project)
        url = '/api/project/%s?api_key=%s' % (project.id, owner.api_key)
        payload = project.dictize()
        payload['info'] = {'foo': 'bar'}
        payload['info'].update({key: None for key in old_info.keys()})
        del payload['id']
        del payload['created']
        del payload['updated']
        del payload['contacted']
        del payload['published']
        del payload['owner_id']
        del payload['secret_key']
        res = self.app.put(url, data=json.dumps(payload))
        project = project_repo.get(project.id)

        for key, value in old_info.iteritems():
            if not payload['info'].get(key):
                assert project.info.get(key) == value

    @with_context
    def test_project_post_no_access_levels(self):
        """Test API project post successful when no access levels set"""

        user, subadmin = UserFactory.create_batch(2)
        make_subadmin(subadmin)
        CategoryFactory.create()
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project',
            description='description',
            owner_id=1,
            long_description=u'Long Description\n================',
            password="hello",
            info=dict(
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=0.5,
                product="abc",
                subproduct="def",
            ))
        data = json.dumps(data)

        res = self.app.post('/api/project?api_key=' + subadmin.api_key,
                            data=data)
        out = project_repo.get_by(name=name)
        assert out, out
        assert_equal(out.short_name, 'xxxx-project'), out
        assert_equal(out.owner.name, 'user2')
        assert_equal(out.owners_ids, [2])

    @with_context
    def test_project_can_post_valid_project_levels(self):
        """Test API project create can set correct data access levels"""

        from pybossa import data_access

        users = UserFactory.create_batch(2, info=dict(data_access=['L1']))
        make_subadmin(users[1])

        project_levels = ['L4']
        project_users = [users[0].id, users[1].id]
        CategoryFactory.create()
        name = u'My Project'
        headers = [('Authorization', users[1].api_key)]
        new_project = dict(
            name=name,
            short_name='my-project',
            description='my-project-description',
            owner_id=1,
            long_description=u'my project\nlong description',
            password='hello',
            info=dict(
                data_access=project_levels,
                project_users=project_users,
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=0.5,
                product="abc",
                subproduct="def",
                ))
        new_project = json.dumps(new_project)

        with patch.dict(data_access.data_access_levels, self.patch_data_access_levels):
            res = self.app.post('/api/project', headers=headers,
                                data=new_project)
            data = json.loads(res.data)['info']
            assert res.status_code == 200, 'project access levels should have been set'
            assert data['data_access'] == project_levels
            assert data['project_users'] == project_users

            # test update
            project = project_repo.get_by(name=name)
            assert project, project
            assert_equal(project.short_name, 'my-project'), project
            project_id = project.id

            new_project_levels = ["L3"]
            new_project_users = [users[1].id]
            data = dict(
                name=name,
                short_name='my-project',
                description='my-project-description',
                info=dict(
                project_users=new_project_users,
                data_classification=dict(input_data="L3 - community", output_data="L4 - public")
            ))
            new_data = json.dumps(data)
            res = self.app.put('/api/project/%s' % project_id, headers=headers, data=new_data)
            assert res.status_code == 200, 'project access levels should have been set'
            data = json.loads(res.data)['info']
            assert data['data_access'] == new_project_levels
            assert data['project_users'] == new_project_users


    @with_context
    def test_project_cannot_post_invalid_project_levels(self):
        """Test API project create cannot set invalid data access levels"""

        from pybossa import data_access

        users = UserFactory.create_batch(2, info=dict(data_access=['L1']))
        make_subadmin(users[1])

        project_levels = ['BAD']
        project_users = [users[0].id, users[1].id]

        name = u'My Project'
        headers = [('Authorization', users[1].api_key)]
        new_project = dict(
            name=name,
            short_name='my-project',
            description='my-project-description',
            owner_id=1,
            long_description=u'my project\nlong description',
            password='hello',
            info=dict(data_access=project_levels, project_users=project_users))
        new_project = json.dumps(new_project)

        with patch.dict(data_access.data_access_levels, self.patch_data_access_levels):
            res = self.app.post('/api/project', headers=headers,
                                data=new_project, follow_redirects=True)
            error = json.loads(res.data)
            assert res.status_code == 415, res.status_code
            assert error['status'] == 'failed', error
            assert error['action'] == 'POST', error
            assert error['target'] == 'project', error
            assert error['exception_cls'] == 'ValueError', error
            message = u'Invalid access levels {}'.format(', '.join(project_levels))
            assert error['exception_msg'] == message, error

    @with_context
    def test_project_cannot_assign_users_with_mismatched_access_levels(self):
        """Test API project post cannot set users with data access levels that doesnt match project access levels"""

        from pybossa import data_access

        users = UserFactory.create_batch(2, info=dict(data_access=['L3']))
        make_subadmin(users[1])

        project_levels = ['L1']
        project_users = [users[0].id, users[1].id]

        CategoryFactory.create()
        name = u'My Project'
        headers = [('Authorization', users[1].api_key)]
        new_project = dict(
            name=name,
            short_name='my-project',
            description='my-project-description',
            owner_id=1,
            long_description=u'my project\nlong description',
            password='hello',
            info=dict(
                data_access=project_levels, 
                project_users=project_users,
                product="abc",
                subproduct="def",
                )
            )
        new_project = json.dumps(new_project)

        with patch.dict(data_access.data_access_levels, self.patch_data_access_levels):
            res = self.app.post('/api/project', headers=headers,
                                data=new_project, follow_redirects=True)

            error = json.loads(res.data)
            assert res.status_code == 415, res.status_code
            assert error['status'] == 'failed', error
            assert error['action'] == 'POST', error
            assert error['target'] == 'project', error
            assert error['exception_cls'] == 'ValueError', error
            message = u'Data access level mismatch. Cannot assign user {} to project'.format(', '.join(map(str, project_users)))
            assert error['exception_msg'] == message, error


    @with_context
    def test_project_get_works_with_and_without_data_access(self):
        """Test API project get cannot access project when user is not assigned to the project although user data_access match projects"""

        from pybossa.api.user import data_access

        owner = UserFactory.create(admin=True)
        # user_l1 = UserFactory.create(info=dict(data_access=['L1']))
        # user_l3 = UserFactory.create(info=dict(data_access=['L3']))
        user_l3 = UserFactory.create(info=dict(data_access=['L3']))
        user_l4 = UserFactory.create(info=dict(data_access=['L4']))

        # project = ProjectFactory.create(owner=owner, info=dict(data_access=["L1", "L2"]))
        project = ProjectFactory.create(
            owner=owner,
            info=dict(data_classification=dict(input_data="L3 - community", output_data="L3 - community")
        ))

        self.set_proj_passwd_cookie(project, user_l3)
        # without data_access, user should be able to get project
        res = self.app.get(u'api/project/{}?api_key={}'.format(project.id, user_l3.api_key))
        assert res.status_code == 200, 'without data access, user should get project with project password'

        # with data_access, user should not be able to get project unless user is assigned to project
        with patch.dict(data_access.data_access_levels, self.patch_data_access_levels):
            # res = self.app.get(u'api/project/{}?api_key={}'.format(project.id, user_l1.api_key))
            res = self.app.get(u'api/project/{}?api_key={}'.format(project.id, user_l3.api_key))
            assert_equal(res.status, '403 FORBIDDEN', 'without data access, user should get project with project password')

            # assign user to project
            project.info['project_users'] = [user_l3.id]
            project_repo.update(project)
            res = self.app.get(u'api/project/{}?api_key={}'.format(project.id, user_l3.api_key))
            assert res.status_code == 200, 'user assigned to project should have obtained project'
            data = json.loads(res.data)
            assert data['short_name'] == project.short_name


    @with_context
    def test_project_filter_by_category_works(self):
        """Test API project filter by category works."""
        users = UserFactory.create_batch(1, info=dict())
        make_subadmin(users[0])
        category = CategoryFactory.create()
        projects_published = ProjectFactory.create_batch(2,
                                                         published=True,
                                                         category=category)
        projects_not_published = ProjectFactory.create_batch(2,
                                                             published=False,
                                                             category=category)
        headers = [('Authorization', users[0].api_key)]
        res = self.app.get('/api/project?all=1&category_id=%s' % category.id, headers=headers)
        data = json.loads(res.data)
        assert len(data) == 4, data

    @with_context
    def test_project_post_without_password_fails(self):
        """Test project creation via API without password fails"""
        user = UserFactory.create()
        headers = [('Authorization', user.api_key)]
        data = dict(
            name="nopassword",
            short_name="nopassword",
            long_description="nopassword",
            info=dict(
                data_classification=dict(input_data="L4 - public", output_data="L4 - public")
            ))
        res = self.app.post('/api/project', headers=headers,
                            data=json.dumps(data))
        err = json.loads(res.data)
        err_msg = "password required"
        assert err['action'] == 'POST', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == "BadRequest", err_msg
        assert res.status_code == 400, err_msg

    @with_context
    def test_project_post_desc_from_long_desc(self):
        user = UserFactory.create()
        headers = [('Authorization', user.api_key)]
        CategoryFactory.create()
        data = dict(
            name="longdesctest",
            short_name="longdesctest",
            long_description="<HTMLTAG>" + ("a" * 300),
            password="exists",
            info=dict(
                data_classification=dict(input_data="L3 - community", output_data="L4 - public"),
                kpi=1,
                product="abc",
                subproduct="def"
            ))
        res = self.app.post('/api/project', headers=headers,
                            data=json.dumps(data))
        res_data = json.loads(res.data)
        assert res.status_code == 200

        # password is removed
        assert "password" not in res_data
        # check description was formatted
        assert len(res_data["description"]) == 255
        assert res_data["description"][-3:] == "..."
        assert res_data["description"].startswith("a")
        # check that data access was set appropriately
        assert res_data["info"]["data_access"] == ["L3"]

    @with_context
    def test_project_post_kpi_out_of_range(self):
        user = UserFactory.create()
        CategoryFactory.create()
        # test create kpi out of range
        headers = [('Authorization', user.api_key)]
        data = dict(
            name="kpitest",
            short_name="kpitest",
            long_description="kpitest",
            password="exists",
            info=dict(
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=121
            ))
        res = self.app.post('/api/project', headers=headers,
                            data=json.dumps(data))
        err = json.loads(res.data)
        err_msg = "KPI must be value between 0.1 and 120"
        assert err['action'] == 'POST', err_msg
        assert err['status'] == 'failed', err_msg
        assert err['exception_cls'] == "BadRequest", err_msg
        assert res.status_code == 400, err_msg

    @with_context
    def test_project_post_from_sync(self):
        user = UserFactory.create()
        CategoryFactory.create()
        # test create kpi out of range
        headers = [('Authorization', user.api_key)]
        data = dict(
            name='my-project',
            short_name='my-project',
            description='my-project-description',
            info=dict(
                data_classification=dict(input_data="L4 - public", output_data="L4 - public"),
                kpi=50,
                sync=dict(latest_sync="latest_sync",
                      source_url="test.com",
                      syncer="test@test.com",
                      enabled=True),
                passwd_hash = "hashpwd",
                product="abc",
                subproduct="def",
        ))
        res = self.app.post('/api/project', headers=headers,
                            data=json.dumps(data))
        res_data = json.loads(res.data)
        assert res.status_code == 200

    @with_context
    def test_project_post_amp_pvf(self):
        user = UserFactory.create()
        CategoryFactory.create()
        headers = [('Authorization', user.api_key)]
        # post empty pvf for L1 to result into error
        data = dict(
            name='got',
            short_name='gameofthrones',
            description='winter is coming',
            password = "dragonglass",
            info=dict(
                data_classification=dict(input_data="L1 - internal valid", output_data="L3 - community"),
                kpi=0.5,
                product="abc",
                subproduct="def",
                annotation_config=dict(amp_store=True, amp_pvf='')
        ))
        res = self.app.post('/api/project', headers=headers,
                            data=json.dumps(data))
        res_data = json.loads(res.data)
        assert res.status_code == 400
        error_msg = res_data['exception_msg']
        assert error_msg == "Invalid PVF format. Must contain <PVF name> <PVF val>.", error_msg

        # post bad pvf for L1 to result into failure
        data["info"]["annotation_config"]["amp_pvf"] = "xxxx yyyy zzzz"
        res = self.app.post('/api/project', headers=headers,
                            data=json.dumps(data))
        res_data = json.loads(res.data)
        assert res.status_code == 400
        error_msg = res_data['exception_msg']
        assert error_msg == "Invalid PVF format. Must contain <PVF name> <PVF val>.", error_msg

        # post valid pvf for L1 to result into success
        data["info"]["annotation_config"]["amp_pvf"] = "XXX 123"
        res = self.app.post('/api/project', headers=headers,
                            data=json.dumps(data))
        res_data = json.loads(res.data)
        assert res.status_code == 200, "POST project api should be successful"
        assert res_data["info"]["annotation_config"]["amp_pvf"] == "XXX 123", "Project PVF should be set to XXX 123"

        # project w/ public data access and optin checked to have "GIG 200" pvf configured
        data2 = copy.deepcopy(data)
        data2["name"] = "got2"
        data2["short_name"] = "got s2"
        data2["info"]["data_classification"]["input_data"] = "L3 - community"
        res = self.app.post('/api/project', headers=headers,
                            data=json.dumps(data2))
        res_data = json.loads(res.data)
        assert res.status_code == 200, "POST project api should be successful"
        assert res_data["info"]["annotation_config"]["amp_pvf"] == "GIG 200", "Project PVF should be set to GIG 200 for public data."

