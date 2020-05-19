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

from itsdangerous import SignatureExpired
from default import db, with_context
from test_api import TestAPI, get_pwd_cookie
from factories import (ProjectFactory, TaskFactory, UserFactory)
from datetime import datetime, timedelta
from mock import patch


from pybossa.repositories import ProjectRepository
project_repo = ProjectRepository(db)


class TestNewtaskPasswd(TestAPI):

    @with_context
    def test_newtask(self):
        """Test API project new_task method and authentication"""
        project = ProjectFactory.create()
        project.set_password('the_password')
        project_repo.save(project)
        TaskFactory.create_batch(2, project=project, info={'question': 'answer'})
        user = UserFactory.create()

        # anonymous
        # test getting a new task
        res = self.app.get('/api/project/%s/newtask' % project.id)
        assert res, res
        task = json.loads(res.data)
        assert 'error' in task['info'], 'No anonymous contributors'

        # as a real user, no password
        url = '/api/project/%s/newtask?api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url)
        assert res.status_code == 403, res
        task = json.loads(res.data)
        assert task['exception_msg'] == 'No project password provided'

        url = '/project/%s/password?api_key=%s' % (project.short_name, user.api_key)
        data = dict(password='the_password')
        res = self.app.post(url, data=data)

        c, v, e = get_pwd_cookie(project.short_name, res)

        assert c
        self.app.set_cookie('/', c, v)

        url = '/api/project/%s/newtask?api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url)
        assert res.status_code == 200, res
        task = json.loads(res.data)
        assert task['info'].get('question') == 'answer'

    @with_context
    def test_newtask_owner(self):
        """Test API project owner needs no password"""
        project = ProjectFactory.create()
        project.set_password('the_password')
        project_repo.save(project)
        TaskFactory.create_batch(2, project=project, info={'question': 'answer'})
        api_key = project.owner.api_key

        # as a real user, no password
        url = '/api/project/%s/newtask?api_key=%s' % (project.id, api_key)
        res = self.app.get(url)
        assert res.status_code == 200, res
        task = json.loads(res.data)
        assert task['info'].get('question') == 'answer'

    @with_context
    def test_newtask_extends_expiration(self):
        """Test API project new_task extends expiration"""
        project = ProjectFactory.create()
        project.set_password('the_password')
        project_repo.save(project)
        TaskFactory.create_batch(2, project=project, info={'question': 'answer'})
        user = UserFactory.create()

        url = '/project/%s/password?api_key=%s' % (project.short_name, user.api_key)
        data = dict(password='the_password')
        res = self.app.post(url, data=data)

        c, v, e = get_pwd_cookie(project.short_name, res)

        assert c
        self.app.set_cookie('/', c, v)

        now = datetime.utcnow()
        url = '/api/project/%s/newtask?api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url)
        assert res.status_code == 200, res
        task = json.loads(res.data)
        assert task['info'].get('question') == 'answer'

        c, v, new_exp = get_pwd_cookie(project.short_name, res)
        assert e - now < timedelta(minutes=35)
        assert new_exp - now > timedelta(minutes=55)
        assert new_exp - now < timedelta(minutes=65)

    @with_context
    def test_newtask_extends_expiration_by_timeout(self):
        """Test API project new_task extends expiration according to timeout"""
        project = ProjectFactory.create(info={'timeout': 120*60, 'data_classification': dict(input_data="L4 - public", output_data="L4 - public")})
        project.set_password('the_password')
        project_repo.save(project)
        TaskFactory.create_batch(2, project=project, info={'question': 'answer'})
        user = UserFactory.create()

        url = '/project/%s/password?api_key=%s' % (project.short_name, user.api_key)
        data = dict(password='the_password')
        res = self.app.post(url, data=data)

        c, v, e = get_pwd_cookie(project.short_name, res)

        assert c
        self.app.set_cookie('/', c, v)

        now = datetime.utcnow()
        url = '/api/project/%s/newtask?api_key=%s' % (project.id, user.api_key)
        res = self.app.get(url)
        assert res.status_code == 200, (res, res.data)
        task = json.loads(res.data)
        assert task['info'].get('question') == 'answer'

        c, v, new_exp = get_pwd_cookie(project.short_name, res)
        assert new_exp - now > timedelta(minutes=115)
        assert new_exp - now < timedelta(minutes=125)

    @with_context
    def test_newtask_expired_cookie(self):
        """Test API project new_task expired cookie"""
        project = ProjectFactory.create(info={'timeout': 60, 'data_classification': dict(input_data="L4 - public", output_data="L4 - public")})
        project.set_password('the_password')
        project_repo.save(project)
        TaskFactory.create_batch(2, project=project, info={'question': 'answer'})
        user = UserFactory.create()

        # simulate sending expired cookies
        with patch.dict(self.flask_app.config, {'PASSWD_COOKIE_TIMEOUT': -1}):
            url = '/project/%s/password?api_key=%s' % (project.short_name, user.api_key)
            data = dict(password='the_password')
            res = self.app.post(url, data=data)

            c, v, e = get_pwd_cookie(project.short_name, res)

            assert c
            self.app.set_cookie('/', c, v)
            res = self.app.post(url, data=data)
            c, v, e = get_pwd_cookie(project.short_name, res)

            assert c

            url = '/project/%s/newtask?api_key=%s' % (project.short_name, user.api_key)
            res = self.app.get(url)
            assert res.status_code == 302
            headers = {'Content-Type': 'application/json'}
            res = self.app.get(url, headers=headers)
            next_url = json.loads(res.data)['next']
            print next_url
            headers = {'Authorization': user.api_key}
            res = self.app.get(next_url, headers=headers)

            assert 'Enter the password to contribute to this project' in res.data, res.data

    @with_context
    def test_newtask_no_gold_answers(self):
        """Test newtask returns task without gold answers"""
        project = ProjectFactory.create()
        project_repo.save(project)
        TaskFactory.create(project=project, info={'question': 'answer'}, gold_answers={'answer': 1})
        api_key = project.owner.api_key

        # as a real user, no password
        url = '/api/project/%s/newtask?api_key=%s' % (project.id, api_key)
        res = self.app.get(url)
        assert res.status_code == 200, (res, res.data)
        task = json.loads(res.data)
        assert task.get('gold_answers') is None