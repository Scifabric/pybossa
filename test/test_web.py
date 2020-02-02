#-*- coding: utf8 -*-
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

import codecs
import copy
import json
import os
import shutil
import zipfile
import six
import pandas as pd
from io import StringIO, BytesIO
from default import db, Fixtures, with_context, with_context_settings, FakeResponse, mock_contributions_guard
from helper import web
from mock import patch, Mock, call, MagicMock
from flask import redirect
from itsdangerous import BadSignature
from pybossa.util import get_user_signup_method
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
from pandas.errors import EmptyDataError
from pybossa.model.project import Project
from pybossa.model.category import Category
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.user import User
from pybossa.model.result import Result
from pybossa.messages import *
from pybossa.leaderboard.jobs import leaderboard as update_leaderboard
from pybossa.core import user_repo, project_repo, result_repo, signer
from pybossa.jobs import send_mail, import_tasks
from pybossa.importers import ImportReport
from pybossa.cache.project_stats import update_stats
from factories import AnnouncementFactory, ProjectFactory, CategoryFactory, TaskFactory, TaskRunFactory, UserFactory
from unidecode import unidecode
from werkzeug.utils import secure_filename
from nose.tools import assert_raises
from flatten_json import flatten


class TestWeb(web.Helper):
    pkg_json_not_found = {
        "help": "Return ...",
        "success": False,
        "error": {
            "message": "Not found",
            "__type": "Not Found Error"}}

    def clear_temp_container(self, user_id):
        """Helper function which deletes all files in temp folder of a given owner_id"""
        temp_folder = os.path.join('/tmp', 'user_%d' % user_id)
        if os.path.isdir(temp_folder):
            shutil.rmtree(temp_folder)

    @with_context
    def test_01_index(self):
        """Test WEB home page works"""
        res = self.app.get("/", follow_redirects=True)
        assert self.html_title() in str(res.data), res.data
        assert "Create" in str(res.data), res

    @with_context
    def test_01_index_json(self):
        """Test WEB JSON home page works"""
        project = ProjectFactory.create(featured=True)
        res = self.app_get_json("/")
        data = json.loads(res.data)
        keys = ['featured', 'template']
        for key in keys:
            assert key in list(data.keys()), data
        assert len(data['featured']) == 1, data
        assert data['featured'][0]['short_name'] == project.short_name


    @with_context
    def test_01_search(self):
        """Test WEB search page works."""
        res = self.app.get('/search')
        err_msg = "Search page should be accessible"
        assert "Search" in str(res.data), err_msg

    @with_context
    def test_01_search_json(self):
        """Test WEB JSON search page works."""
        res = self.app_get_json('/search')
        err_msg = "Search page should be accessible"
        data = json.loads(res.data)
        assert data.get('template') == '/home/search.html', err_msg


    @with_context
    def test_result_view(self):
        """Test WEB result page works."""
        import os
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        template_folder = os.path.join(APP_ROOT, '..', 'pybossa',
                                       self.flask_app.template_folder)
        file_name = os.path.join(template_folder, "home", "_results.html")
        mode = "w+b"
        if six.PY2:
            mode = "w"
        with open(file_name, mode) as f:
            f.write(b"foobar")
        res = self.app.get('/results')
        assert b"foobar" in res.data, res.data
        os.remove(file_name)


    @with_context
    def test_result_view_json(self):
        """Test WEB JSON result page works."""
        import os
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        template_folder = os.path.join(APP_ROOT, '..', 'pybossa',
                                       self.flask_app.template_folder)
        file_name = os.path.join(template_folder, "home", "_results.html")
        mode = "w+b"
        if six.PY2:
            mode = "w"
        with open(file_name, mode) as f:
            f.write(b"foobar")
        res = self.app_get_json('/results')
        data = json.loads(res.data)
        assert data.get('template') == '/home/_results.html', data
        os.remove(file_name)


    @with_context
    def test_00000_results_not_found(self):
        """Test WEB results page returns 404 when no template is found works."""
        res = self.app.get('/results')
        assert res.status_code == 404, res.data

    @with_context
    def test_leaderboard(self):
        """Test WEB leaderboard works"""
        user = UserFactory.create()
        TaskRunFactory.create(user=user)
        update_leaderboard()
        res = self.app.get('/leaderboard', follow_redirects=True)
        assert self.html_title("Community Leaderboard") in str(res.data), res
        assert user.name in str(res.data), res.data
        assert_raises(ValueError, json.loads, res.data)

    @with_context
    def test_leaderboard_json(self):
        """Test leaderboard json works"""
        user = UserFactory.create()
        TaskRunFactory.create(user=user)
        TaskRunFactory.create(user=user)
        update_leaderboard()
        res = self.app_get_json('/leaderboard/')
        data = json.loads(res.data)
        err_msg = 'Template wrong'
        assert data['template'] == '/stats/index.html', err_msg
        err_msg = 'Title wrong'
        assert data['title'] == 'Community Leaderboard', err_msg
        err_msg = 'Top users missing'
        assert 'top_users' in str(data), err_msg
        err_msg = 'leaderboard user information missing'
        first_user = data['top_users'][0]
        assert 'created' in first_user, err_msg
        assert first_user['fullname'] == 'User 1', err_msg
        assert first_user['name'] == 'user1', err_msg
        assert first_user['rank'] == 1, err_msg
        assert first_user['score'] == 2, err_msg
        assert 'registered_ago' in first_user, err_msg
        assert 'n_answers' in first_user, err_msg
        assert 'info' in first_user, err_msg
        assert 'avatar' in first_user['info'], err_msg
        assert 'container' in first_user['info'], err_msg
        err_msg = 'privacy leak in user information'
        assert 'id' not in first_user, err_msg
        assert 'api_key' not in first_user, err_msg

        users = UserFactory.create_batch(40)
        for u in users[0:22]:
            TaskRunFactory.create(user=u)
            TaskRunFactory.create(user=u)
            TaskRunFactory.create(user=u)
            TaskRunFactory.create(user=u)

        for u in users[22:28]:
            TaskRunFactory.create(user=u)
            TaskRunFactory.create(user=u)
            TaskRunFactory.create(user=u)

        update_leaderboard()

        for score in range(1, 11):
            UserFactory.create(info=dict(n=score))

        update_leaderboard(info='n')

        res = self.app_get_json('/leaderboard/window/3?api_key=%s' % user.api_key)
        data = json.loads(res.data)
        err_msg = 'Top users missing'
        assert 'top_users' in str(data), err_msg
        err_msg = 'leaderboard user information missing'
        leaders = data['top_users']
        assert len(leaders) == (20+3+1+3), len(leaders)
        assert leaders[23]['name'] == user.name

        res = self.app_get_json('/leaderboard/window/11?api_key=%s' % user.api_key)
        data = json.loads(res.data)
        err_msg = 'Top users missing'
        assert 'top_users' in str(data), err_msg
        err_msg = 'leaderboard user information missing'
        leaders = data['top_users']
        assert len(leaders) == (20+10+1+10), len(leaders)
        assert leaders[30]['name'] == user.name

        res = self.app_get_json('/leaderboard/?info=noleaderboards')
        assert res.status_code == 404,  res.status_code

        with patch.dict(self.flask_app.config, {'LEADERBOARDS': ['n']}):
            res = self.app_get_json('/leaderboard/?info=n')
            data = json.loads(res.data)
            err_msg = 'Top users missing'
            assert 'top_users' in str(data), err_msg
            err_msg = 'leaderboard user information missing'
            leaders = data['top_users']
            assert len(leaders) == (20), len(leaders)
            score = 10
            rank = 1
            for u in leaders[0:10]:
                assert u['score'] == score, u
                assert u['rank'] == rank, u
                score = score - 1
                rank = rank + 1

            res = self.app_get_json('/leaderboard/window/3?api_key=%s&info=n' % user.api_key)
            data = json.loads(res.data)
            err_msg = 'Top users missing'
            assert 'top_users' in str(data), err_msg
            err_msg = 'leaderboard user information missing'
            leaders = data['top_users']
            assert len(leaders) == (20+3+1+3), len(leaders)
            assert leaders[23]['name'] == user.name
            assert leaders[23]['score'] == 0

            res = self.app_get_json('/leaderboard/?info=new')
            assert res.status_code == 404,  res.status_code


    @with_context
    def test_announcement_json(self):
        """Test public announcements"""
        url = '/announcements/'
        err_msg = "It should return 200"
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert res.status_code == 200, err_msg
        assert "announcements" in list(data.keys()), data
        assert "template" in list(data.keys()), data
        # create an announcement in DB
        announcement = AnnouncementFactory.create()
        res = self.app_get_json(url)
        data = json.loads(res.data)
        announcement0 = data['announcements'][0]
        assert announcement0['body'] == 'Announcement body text'
        assert announcement0['title'] == 'Announcement title'
        assert announcement0['id'] == 1

    @with_context
    def test_project_stats(self):
        """Test WEB project stats page works"""
        res = self.register()
        res = self.signin()
        res = self.new_project(short_name="igil")

        project = db.session.query(Project).first()
        user = db.session.query(User).first()
        # Without stats
        url = '/project/%s/stats' % project.short_name
        res = self.app.get(url)
        assert "Sorry" in str(res.data), res.data

        # We use a string here to check that it works too
        task = Task(project_id=project.id, n_answers=10)
        db.session.add(task)
        db.session.commit()

        for i in range(10):
            task_run = TaskRun(project_id=project.id, task_id=1,
                               user_id=user.id,
                               info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()
            res = self.app.get('api/project/%s/newtask' % project.id)

        # With stats
        url = '/project/%s/stats' % project.short_name
        update_stats(project.id)
        res = self.app.get(url)
        assert res.status_code == 200, res.status_code
        assert "Distribution" in str(res.data), res.data

    @with_context
    def test_project_stats_json(self):
        """Test WEB project stats page works JSON"""
        res = self.register()
        res = self.signin()
        res = self.new_project(short_name="igil")

        project = db.session.query(Project).first()
        user = db.session.query(User).first()
        # Without stats
        url = '/project/%s/stats' % project.short_name
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = 'Field should not be present'
        assert 'avg_contrib_time' not in str(data), err_msg
        assert 'projectStats' not in str(data), err_msg
        assert 'userStats' not in str(data), err_msg
        err_msg = 'Field should be present'
        assert 'n_completed_tasks' in str(data), err_msg
        assert 'n_tasks' in str(data), err_msg
        assert 'n_volunteers' in str(data), err_msg
        assert 'overall_progress' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'pro_features' in str(data), err_msg
        assert 'project' in str(data), err_msg
        err_msg = 'Field should not be private'
        assert 'id' in data['owner'], err_msg
        assert 'api_key' in data['owner'], err_msg
        assert 'secret_key' in data['project'], err_msg
        assert res.status_code == 200, res.status_code

        # We use a string here to check that it works too
        task = Task(project_id=project.id, n_answers=10)
        db.session.add(task)
        db.session.commit()

        for i in range(10):
            task_run = TaskRun(project_id=project.id, task_id=1,
                               user_id=user.id,
                               info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()
            self.app_get_json('api/project/%s/newtask' % project.id)

        # With stats
        update_stats(project.id)

        url = '/project/%s/stats' % project.short_name
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = 'Field missing in JSON response'
        assert 'avg_contrib_time' in str(data), (err_msg, list(data.keys()))
        assert 'n_completed_tasks' in str(data), err_msg
        assert 'n_tasks' in str(data), err_msg
        assert 'n_volunteers' in str(data), err_msg
        assert 'overall_progress' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'pro_features' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'projectStats' in str(data), err_msg
        assert 'userStats' in str(data), err_msg
        err_msg = 'Field should not be private'
        assert 'id' in data['owner'], err_msg
        assert 'api_key' in data['owner'], err_msg
        assert 'secret_key' in data['project'], err_msg
        assert res.status_code == 200, res.status_code

        url = '/project/%s/stats' % project.short_name
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = 'Field missing in JSON response'
        assert 'avg_contrib_time' in str(data), err_msg
        assert 'n_completed_tasks' in str(data), err_msg
        assert 'n_tasks' in str(data), err_msg
        assert 'n_volunteers' in str(data), err_msg
        assert 'overall_progress' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'pro_features' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'projectStats' in str(data), err_msg
        assert 'userStats' in str(data), err_msg
        err_msg = 'Field should not be private'
        assert 'id' in data['owner'], err_msg
        assert 'api_key' in data['owner'], err_msg
        assert 'secret_key' in data['project'], err_msg
        assert res.status_code == 200, res.status_code
        err_msg = 'there should not have geo data'
        assert data['userStats'].get('geo') == None, err_msg


    @with_context
    def test_contribution_time_shown_for_admins_for_every_project(self):
        admin = UserFactory.create(admin=True)
        admin.set_password('1234')
        user_repo.save(admin)
        owner = UserFactory.create(pro=False)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create(project=project)
        TaskRunFactory.create(task=task)
        update_stats(project.id)
        url = '/project/%s/stats' % project.short_name
        self.signin(email=admin.email_addr, password='1234')
        res = self.app.get(url)
        assert_raises(ValueError, json.loads, res.data)
        assert 'Average contribution time' in str(res.data)


    @with_context
    def test_contribution_time_shown_for_admins_for_every_project_json(self):
        admin = UserFactory.create(admin=True)
        admin.set_password('1234')
        user_repo.save(admin)
        owner = UserFactory.create(pro=False)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create(project=project)
        TaskRunFactory.create(task=task)
        url = '/project/%s/stats' % project.short_name
        self.signin(email=admin.email_addr, password='1234')
        update_stats(project.id)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = 'Field missing in JSON response'
        assert 'avg_contrib_time' in str(data), err_msg
        assert 'n_completed_tasks' in str(data), err_msg
        assert 'n_tasks' in str(data), err_msg
        assert 'n_volunteers' in str(data), err_msg
        assert 'overall_progress' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'pro_features' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'projectStats' in str(data), err_msg
        assert 'userStats' in str(data), err_msg
        err_msg = 'Field should be private'
        assert 'id' not in data['owner'], err_msg
        assert 'api_key' not in data['owner'], err_msg
        assert 'secret_key' not in data['project'], err_msg


    @with_context
    def test_contribution_time_shown_in_pro_owned_projects(self):
        pro_owner = UserFactory.create(pro=True)
        pro_owned_project = ProjectFactory.create(owner=pro_owner)
        task = TaskFactory.create(project=pro_owned_project)
        TaskRunFactory.create(task=task)
        update_stats(task.project.id)
        pro_url = '/project/%s/stats' % pro_owned_project.short_name
        res = self.app.get(pro_url)
        assert_raises(ValueError, json.loads, res.data)
        assert 'Average contribution time' in str(res.data)

    @with_context
    def test_contribution_time_shown_in_pro_owned_projects_json(self):
        pro_owner = UserFactory.create(pro=True)
        pro_owned_project = ProjectFactory.create(owner=pro_owner)
        task = TaskFactory.create(project=pro_owned_project)
        TaskRunFactory.create(task=task)
        update_stats(task.project.id)
        pro_url = '/project/%s/stats' % pro_owned_project.short_name

        res = self.app_get_json(pro_url)
        data = json.loads(res.data)
        err_msg = 'Field missing in JSON response'
        assert 'avg_contrib_time' in str(data), err_msg
        assert 'n_completed_tasks' in str(data), err_msg
        assert 'n_tasks' in str(data), err_msg
        assert 'n_volunteers' in str(data), err_msg
        assert 'overall_progress' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'pro_features' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'projectStats' in str(data), err_msg
        assert 'userStats' in str(data), err_msg
        err_msg = 'Field should be private'
        assert 'id' not in data['owner'], err_msg
        assert 'api_key' not in data['owner'], err_msg
        assert 'secret_key' not in data['project'], err_msg

    @with_context
    def test_contribution_time_not_shown_in_regular_user_owned_projects(self):
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        TaskRunFactory.create(task=task)
        url = '/project/%s/stats' % project.short_name
        res = self.app.get(url)
        assert_raises(ValueError, json.loads, res.data)
        assert 'Average contribution time'  not in str(res.data)

    @with_context
    def test_contribution_time_not_shown_in_regular_user_owned_projects_json(self):
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        TaskRunFactory.create(task=task)
        url = '/project/%s/stats' % project.short_name

        update_stats(project.id)

        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = 'Field missing in JSON response'
        assert 'avg_contrib_time' in str(data), err_msg
        assert 'n_completed_tasks' in str(data), err_msg
        assert 'n_tasks' in str(data), err_msg
        assert 'n_volunteers' in str(data), err_msg
        assert 'overall_progress' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'pro_features' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'projectStats' in str(data), err_msg
        assert 'userStats' in str(data), err_msg
        err_msg = 'Field should be private'
        assert 'id' not in data['owner'], err_msg
        assert 'api_key' not in data['owner'], err_msg
        assert 'secret_key' not in data['project'], err_msg

    @with_context
    def test_03_account_index(self):
        """Test WEB account index works."""
        # Without users
        res = self.app.get('/account/page/15', follow_redirects=True)
        assert res.status_code == 404, res.status_code

        self.create()
        res = self.app.get('/account', follow_redirects=True)
        assert res.status_code == 200, res.status_code
        err_msg = "There should be a Community page"
        assert "Community" in str(res.data), err_msg

    @with_context
    def test_03_account_index_json(self):
        """Test WEB account index JSON works."""
        # Without users
        res = self.app.get('/account/page/15',
                           content_type='application/json')
        assert res.status_code == 404, res.status_code
        data = json.loads(res.data)
        assert data['code'] == 404, res.status_code

        self.create()
        res = self.app_get_json('/account/')
        print(res.data)
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        err_msg = "There should be a Community page"
        assert data['title'] == 'Community', err_msg
        err_msg = "There should be a next, prev item in pagination"
        assert data['pagination']['next'] is False, err_msg
        assert data['pagination']['prev'] is False, err_msg
        assert data['pagination']['per_page'] == 24, err_msg
        # page 1 should also work
        res = self.app_get_json('/account/page/1')
        print(res.data)
        data = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        err_msg = "There should be a Community page"
        assert data['title'] == 'Community', err_msg
        err_msg = "There should be a next, prev item in pagination"
        assert data['pagination']['next'] is False, err_msg
        assert data['pagination']['prev'] is False, err_msg
        assert data['pagination']['per_page'] == 24, err_msg


    @with_context
    def test_register_get(self):
        """Test WEB register user works"""
        res = self.app.get('/account/register')
        # The output should have a mime-type: text/html
        assert res.mimetype == 'text/html', res
        assert self.html_title("Register") in str(res.data), res

    @with_context
    def test_register_get_json(self):
        """Test WEB register JSON user works"""
        from pybossa.forms.account_view_forms import RegisterForm
        res = self.app.get('/account/register',
                           content_type='application/json')
        data = json.loads(res.data)

        form = RegisterForm()
        expected_fields = list(form.data.keys())

        err_msg = "There should be a form"
        assert data.get('form'), err_msg
        for field in expected_fields:
            err_msg = "%s form field is missing"
            assert field in list(data.get('form').keys()), err_msg
        err_msg = "There should be a CSRF field"
        assert data.get('form').get('csrf'), err_msg
        err_msg = "There should be no errors"
        assert data.get('form').get('errors') == {}, err_msg
        err_msg = "There should be a template field"
        assert data.get('template') == 'account/register.html', err_msg
        err_msg = "There should be a title"
        assert data.get('title') == 'Register', err_msg


    @with_context
    def test_register_errors_get(self):
        """Test WEB register errors works"""
        userdict = {'fullname': 'a', 'name': 'name',
                    'email_addr': None, 'password':'p'}
        res = self.app.post('/account/register', data=userdict)
        # The output should have a mime-type: text/html
        assert res.mimetype == 'text/html', res
        assert "correct the errors" in str(res.data), res.data


    @with_context
    def test_register_wrong_content_type(self):
        """Test WEB Register JSON wrong content type."""
        with patch.dict(self.flask_app.config, {'WTF_CSRF_ENABLED': True}):
            url = '/account/register'
            csrf = self.get_csrf(url)
            userdict = {'fullname': 'a', 'name': 'name',
                       'email_addr': None, 'password': 'p'}

            res = self.app.post('/account/register', data=userdict,
                                content_type='application/json',
                                headers={'X-CSRFToken': csrf})
            errors = json.loads(res.data)
            assert errors.get('status') == ERROR, errors
            assert errors.get('form').get('name') == '', errors
            assert len(errors.get('form').get('errors').get('email_addr')) > 0, errors

            res = self.app_post_json(url, data="{stringoftext")
            data = json.loads(res.data)
            err_msg = "The browser (or proxy) sent a request that this server could not understand."
            assert res.status_code == 400, data
            assert data.get('code') == 400, data
            assert data.get('description') == err_msg, data

            data = json.dumps(userdict)
            data += "}"
            print(data)
            res = self.app.post('/account/register', data=data,
                                content_type='application/json',
                                headers={'X-CSRFToken': csrf})
            data = json.loads(res.data)
            assert res.status_code == 400, data
            assert data.get('code') == 400, data
            assert data.get('description') == err_msg, data

    @with_context
    def test_register_csrf_missing(self):
        """Test WEB Register JSON CSRF token missing."""
        with patch.dict(self.flask_app.config, {'WTF_CSRF_ENABLED': True}):
            userdict = {'fullname': 'a', 'name': 'name',
                       'email_addr': None, 'password': 'p'}

            res = self.app.post('/account/register', data=json.dumps(userdict),
                                content_type='application/json')
            errors = json.loads(res.data)
            err_msg = "CSRF validation failed."
            assert errors.get('description') == err_msg, err_msg
            err_msg = "Error code should be 400"
            assert errors.get('code') == 400, err_msg
            assert res.status_code == 400, err_msg


    @with_context
    def test_register_csrf_wrong(self):
        """Test WEB Register JSON CSRF token wrong."""
        with patch.dict(self.flask_app.config, {'WTF_CSRF_ENABLED': True}):
            userdict = {'fullname': 'a', 'name': 'name',
                       'email_addr': None, 'password': 'p'}

            res = self.app.post('/account/register', data=json.dumps(userdict),
                                content_type='application/json',
                                headers={'X-CSRFToken': 'wrong'})
            errors = json.loads(res.data)
            err_msg = "CSRF validation failed."
            assert errors.get('description') == err_msg, err_msg
            err_msg = "Error code should be 400"
            assert errors.get('code') == 400, err_msg
            assert res.status_code == 400, err_msg


    @with_context
    def test_register_json_errors_get(self):
        """Test WEB register errors JSON works"""
        with patch.dict(self.flask_app.config, {'WTF_CSRF_ENABLED': True}):
            csrf = self.get_csrf('/account/register')

            userdict = {'fullname': 'a', 'name': 'name',
                        'email_addr': None, 'password': 'p'}

            res = self.app.post('/account/register', data=json.dumps(userdict),
                                content_type='application/json',
                                headers={'X-CSRFToken': csrf})
            # The output should have a mime-type: application/json
            errors = json.loads(res.data).get('form').get('errors')
            assert res.mimetype == 'application/json', res.data
            err_msg = "There should be an error with the email"
            assert errors.get('email_addr'), err_msg
            err_msg = "There should be an error with fullname"
            assert errors.get('fullname'), err_msg
            err_msg = "There should be an error with password"
            assert errors.get('password'), err_msg
            err_msg = "There should NOT be an error with name"
            assert errors.get('name') is None, err_msg


    @with_context
    @patch('pybossa.view.account.mail_queue', autospec=True)
    @patch('pybossa.view.account.render_template')
    @patch('pybossa.view.account.signer')
    def test_register_post_creates_email_with_link(self, signer, render, queue):
        """Test WEB register post creates and sends the confirmation email if
        account validation is enabled"""
        from flask import current_app
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        data = dict(fullname="AJohn Doe", name="johndoe",
                    password="p4ssw0rd", confirm="p4ssw0rd",
                    email_addr="johndoe@example.com",
                    consent=False)
        signer.dumps.return_value = ''
        render.return_value = ''
        res = self.app.post('/account/register', data=data)
        del data['confirm']
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True

        signer.dumps.assert_called_with(data, salt='account-validation')
        render.assert_any_call('/account/email/validate_account.md',
                               user=data,
                               confirm_url='https://localhost/account/register/confirmation?key=')
        assert send_mail == queue.enqueue.call_args[0][0], "send_mail not called"
        mail_data = queue.enqueue.call_args[0][1]
        assert 'subject' in list(mail_data.keys())
        assert 'recipients' in list(mail_data.keys())
        assert 'body' in list(mail_data.keys())
        assert 'html' in list(mail_data.keys())

    @with_context
    @patch('pybossa.view.account.mail_queue', autospec=True)
    @patch('pybossa.view.account.render_template')
    @patch('pybossa.view.account.signer')
    def test_register_post_json_creates_email_with_link(self, signer, render, queue):
        """Test WEB register post JSON creates and sends the confirmation email if
        account validation is enabled"""
        from flask import current_app
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        with patch.dict(self.flask_app.config, {'WTF_CSRF_ENABLED': True}):
            csrf = self.get_csrf('/account/register')
            data = dict(fullname="John Doe", name="johndoe",
                        password="p4ssw0rd", confirm="p4ssw0rd",
                        email_addr="johndoe@example.com",
                        consent=False)
            signer.dumps.return_value = ''
            render.return_value = ''
            res = self.app.post('/account/register', data=json.dumps(data),
                                content_type='application/json',
                                headers={'X-CSRFToken': csrf})
            del data['confirm']
            current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True

            signer.dumps.assert_called_with(data, salt='account-validation')
            render.assert_any_call('/account/email/validate_account.md',
                                   user=data,
                                   confirm_url='https://localhost/account/register/confirmation?key=')
            assert send_mail == queue.enqueue.call_args[0][0], "send_mail not called"
            mail_data = queue.enqueue.call_args[0][1]
            assert 'subject' in list(mail_data.keys())
            assert 'recipients' in list(mail_data.keys())
            assert 'body' in list(mail_data.keys())
            assert 'html' in list(mail_data.keys())


    @with_context
    @patch('pybossa.view.account.mail_queue', autospec=True)
    @patch('pybossa.view.account.render_template')
    @patch('pybossa.view.account.signer')
    def test_update_email_validates_email(self, signer, render, queue):
        """Test WEB update user email creates and sends the confirmation email
        if account validation is enabled"""
        from flask import current_app
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        self.register()
        signer.dumps.return_value = ''
        render.return_value = ''
        self.update_profile(email_addr="new@mail.com")
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        data = dict(fullname="John Doe", name="johndoe",
                    email_addr="new@mail.com")

        signer.dumps.assert_called_with(data, salt='account-validation')
        render.assert_any_call('/account/email/validate_email.md',
                               user=data,
                               confirm_url='https://localhost/account/register/confirmation?key=')
        assert send_mail == queue.enqueue.call_args[0][0], "send_mail not called"
        mail_data = queue.enqueue.call_args[0][1]
        assert 'subject' in list(mail_data.keys())
        assert 'recipients' in list(mail_data.keys())
        assert 'body' in list(mail_data.keys())
        assert 'html' in list(mail_data.keys())
        assert mail_data['recipients'][0] == data['email_addr']
        user = db.session.query(User).get(1)
        msg = "Confirmation email flag not updated"
        assert user.confirmation_email_sent, msg
        msg = "Email not marked as invalid"
        assert user.valid_email is False, msg
        msg = "Email should remain not updated, as it's not been validated"
        assert user.email_addr != 'new@email.com', msg

    @with_context
    def test_register_json(self):
        """Test WEB register JSON creates a new user and logs in."""
        with patch.dict(self.flask_app.config, {'WTF_CSRF_ENABLED': True}):
            csrf = self.get_csrf('/account/register')
            data = dict(fullname="John Doe", name="johndoe", password='daniel',
                        email_addr="new@mail.com", confirm='daniel',
                        consent=True)
            res = self.app.post('/account/register', data=json.dumps(data),
                                content_type='application/json',
                                headers={'X-CSRFToken': csrf},
                                follow_redirects=False)
            cookie = self.check_cookie(res, 'remember_token')
            err_msg = "User should be logged in"
            assert "johndoe" in cookie, err_msg
            user = user_repo.get_by(name='johndoe')
            assert user.consent, user
            assert user.name == 'johndoe', user
            assert user.email_addr == 'new@mail.com', user

    @with_context
    def test_register_json_error(self):
        """Test WEB register JSON does not create a new user
        and does not log in."""
        with patch.dict(self.flask_app.config, {'WTF_CSRF_ENABLED': True}):
            csrf = self.get_csrf('/account/register')
            data = dict(fullname="John Doe", name="johndoe", password='daniel',
                        email_addr="new@mailcom", confirm='')
            res = self.app.post('/account/register', data=json.dumps(data),
                                content_type='application/json',
                                headers={'X-CSRFToken': csrf},
                                follow_redirects=False)
            cookie = self.check_cookie(res, 'remember_token')
            err_msg = "User should not be logged in"
            assert cookie is False, err_msg
            errors = json.loads(res.data)
            assert errors.get('form').get('errors').get('password'), err_msg


    @with_context
    def test_confirm_email_returns_404(self):
        """Test WEB confirm_email returns 404 when disabled."""
        res = self.app.get('/account/confir-email', follow_redirects=True)
        assert res.status_code == 404, res.status_code

    @with_context
    @patch('pybossa.view.account.mail_queue', autospec=True)
    @patch('pybossa.view.account.render_template')
    @patch('pybossa.view.account.signer')
    def test_validate_email(self, signer, render, queue):
        """Test WEB validate email sends the confirmation email
        if account validation is enabled"""
        from flask import current_app
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        self.register()
        user = db.session.query(User).get(1)
        user.valid_email = False
        db.session.commit()
        signer.dumps.return_value = ''
        render.return_value = ''
        data = dict(fullname=user.fullname, name=user.name,
                    email_addr=user.email_addr)

        res = self.app.get('/account/confirm-email', follow_redirects=True)
        signer.dumps.assert_called_with(data, salt='account-validation')
        render.assert_any_call('/account/email/validate_email.md',
                               user=data,
                               confirm_url='https://localhost/account/register/confirmation?key=')
        assert send_mail == queue.enqueue.call_args[0][0], "send_mail not called"
        mail_data = queue.enqueue.call_args[0][1]
        assert 'subject' in list(mail_data.keys())
        assert 'recipients' in list(mail_data.keys())
        assert 'body' in list(mail_data.keys())
        assert 'html' in list(mail_data.keys())
        assert mail_data['recipients'][0] == data['email_addr']
        user = db.session.query(User).get(1)
        msg = "Confirmation email flag not updated"
        assert user.confirmation_email_sent, msg
        msg = "Email not marked as invalid"
        assert user.valid_email is False, msg
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True

    @with_context
    @patch('pybossa.view.account.mail_queue', autospec=True)
    @patch('pybossa.view.account.render_template')
    @patch('pybossa.view.account.signer')
    def test_validate_email_json(self, signer, render, queue):
        """Test WEB validate email sends the confirmation email
        if account validation is enabled"""
        from flask import current_app
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        self.register()
        user = db.session.query(User).get(1)
        user.valid_email = False
        db.session.commit()
        signer.dumps.return_value = ''
        render.return_value = ''
        data = dict(fullname=user.fullname, name=user.name,
                    email_addr=user.email_addr)

        res = self.app_get_json('/account/confirm-email')

        signer.dumps.assert_called_with(data, salt='account-validation')
        render.assert_any_call('/account/email/validate_email.md',
                               user=data,
                               confirm_url='https://localhost/account/register/confirmation?key=')
        assert send_mail == queue.enqueue.call_args[0][0], "send_mail not called"
        mail_data = queue.enqueue.call_args[0][1]
        assert 'subject' in list(mail_data.keys())
        assert 'recipients' in list(mail_data.keys())
        assert 'body' in list(mail_data.keys())
        assert 'html' in list(mail_data.keys())
        assert mail_data['recipients'][0] == data['email_addr']
        user = db.session.query(User).get(1)
        msg = "Confirmation email flag not updated"
        assert user.confirmation_email_sent, msg
        msg = "Email not marked as invalid"
        assert user.valid_email is False, msg
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        # JSON validation
        data = json.loads(res.data)
        assert data.get('status') == INFO, data
        assert "An e-mail has been sent to" in data.get('flash'), data
        assert data.get('next') == '/account/' + user.name + "/", data


    @with_context
    def test_register_post_valid_data_validation_enabled(self):
        """Test WEB register post with valid form data and account validation
        enabled"""
        from flask import current_app
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        data = dict(fullname="John Doe", name="johndoe",
                    password="p4ssw0rd", confirm="p4ssw0rd",
                    email_addr="johndoe@example.com")

        res = self.app.post('/account/register', data=data)
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        assert "Account validation" in str(res.data), res
        assert "Just one more step, please" in str(res.data), res.data
        assert_raises(ValueError, json.loads, res.data)

    @with_context
    def test_register_post_valid_data_validation_enabled_json(self):
        """Test WEB register post with valid form data and account validation
        enabled for JSON"""
        from flask import current_app
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        data = dict(fullname="John Doe", name="johndoe",
                    password="p4ssw0rd", confirm="p4ssw0rd",
                    email_addr="johndoe@example.com")
        res = self.app_post_json('/account/register', data=data)
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        data = json.loads(res.data)
        assert data['status'] == 'sent'
        assert data['template'] == 'account/account_validation.html'
        assert data['title'] == 'Account validation'

    @with_context
    def test_register_post_valid_data_validation_enabled_wrong_data_json(self):
        """Test WEB register post with valid form data and account validation
        enabled for JSON"""
        from flask import current_app

        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        data = dict(fullname="John Doe", name="johndoe",
                    password="p4ssw0rd", confirm="anotherp4ssw0rd",
                    email_addr="johndoe@example.com")
        res = self.app_post_json('/account/register', data=data)
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        data = json.loads(res.data)
        assert data['status'] == 'error'
        assert data['form']['errors']['password'][0] == 'Passwords must match'

        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        data = dict(fullname="John Doe", name="johndoe",
                    password="p4ssw0rd", confirm="p4ssw0rd")
        res = self.app_post_json('/account/register', data=data)
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        data = json.loads(res.data)
        assert 'email_addr' in data['form']['errors']
        assert data['status'] == 'error'

        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        data = dict(name="johndoe",
                    password="p4ssw0rd", confirm="p4ssw0rd",
                    email_addr="johndoe@example.com")
        res = self.app_post_json('/account/register', data=data)
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        data = json.loads(res.data)
        assert 'fullname' in data['form']['errors']
        assert data['status'] == 'error'

        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        data = dict(fullname="John Doe",
                    password="p4ssw0rd", confirm="p4ssw0rd",
                    email_addr="johndoe@example.com")
        res = self.app_post_json('/account/register', data=data)
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        data = json.loads(res.data)
        assert 'name' in data['form']['errors']
        assert data['status'] == 'error'

        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        data = dict(fullname="John Doe", name="johndoe",
                    password="p4ssw0rd", confirm="p4ssw0rd",
                    email_addr="wrongemail")
        res = self.app_post_json('/account/register', data=data)
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        data = json.loads(res.data)
        assert data['status'] == 'error'
        assert data['form']['errors']['email_addr'][0] == 'Invalid email address.'

    @with_context
    @patch('pybossa.util.redirect', wraps=redirect)
    def test_register_post_valid_data_validation_disabled(self, mockredirect):
        """Test WEB register post with valid form data and account validation
        disabled redirects to home page"""
        from flask import current_app
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        data = dict(fullname="John Doe", name="johndoe",
                    password="p4ssw0rd", confirm="p4ssw0rd",
                    email_addr="johndoe@example.com")
        res = self.app.post('/account/register', data=data,
                            follow_redirects=True)
        print(dir(mockredirect))
        mockredirect.assert_called_with('/')

    @with_context
    def test_register_confirmation_fails_without_key(self):
        """Test WEB register confirmation returns 403 if no 'key' param is present"""
        res = self.app.get('/account/register/confirmation')

        assert res.status_code == 403, res.status

    @with_context
    def test_register_confirmation_fails_with_invalid_key(self):
        """Test WEB register confirmation returns 403 if an invalid key is given"""
        res = self.app.get('/account/register/confirmation?key=invalid')

        assert res.status_code == 403, res.status

    @with_context
    @patch('pybossa.view.account.signer')
    def test_register_confirmation_gets_account_data_from_key(self, fake_signer):
        """Test WEB register confirmation gets the account data from the key"""
        exp_time = self.flask_app.config.get('ACCOUNT_LINK_EXPIRATION')
        fake_signer.loads.return_value = dict(fullname='FN', name='name',
                                              email_addr='email',
                                              password='password',
                                              consent=True)
        res = self.app.get('/account/register/confirmation?key=valid-key')

        fake_signer.loads.assert_called_with('valid-key', max_age=exp_time, salt='account-validation')

    @with_context
    @patch('pybossa.view.account.signer')
    def test_register_confirmation_validates_email(self, fake_signer):
        """Test WEB validates email"""
        self.register()
        user = db.session.query(User).get(1)
        user.valid_email = False
        user.confirmation_email_sent = True
        db.session.commit()

        fake_signer.loads.return_value = dict(fullname=user.fullname,
                                              name=user.name,
                                              email_addr=user.email_addr,
                                              consent=False)
        self.app.get('/account/register/confirmation?key=valid-key')

        user = db.session.query(User).get(1)
        assert user is not None
        msg = "Email has not been validated"
        assert user.valid_email, msg
        msg = "Confirmation email flag has not been restored"
        assert user.confirmation_email_sent is False, msg

    @with_context
    @patch('pybossa.view.account.signer')
    def test_register_confirmation_validates_n_updates_email(self, fake_signer):
        """Test WEB validates and updates email"""
        self.register()
        user = db.session.query(User).get(1)
        user.valid_email = False
        user.confirmation_email_sent = True
        db.session.commit()

        fake_signer.loads.return_value = dict(fullname=user.fullname,
                                              name=user.name,
                                              email_addr='new@email.com',
                                              consent=True)
        self.app.get('/account/register/confirmation?key=valid-key')

        user = db.session.query(User).get(1)
        assert user is not None
        msg = "Email has not been validated"
        assert user.valid_email, msg
        msg = "Confirmation email flag has not been restored"
        assert user.confirmation_email_sent is False, msg
        msg = 'Email should be updated after validation.'
        assert user.email_addr == 'new@email.com', msg

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    @patch('pybossa.view.account.url_for')
    @patch('pybossa.view.account.signer')
    def test_confirm_account_newsletter(self, fake_signer, url_for, newsletter):
        """Test WEB confirm email shows newsletter or home."""
        newsletter.ask_user_to_subscribe.return_value = True
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'key'}):
            self.register()
            user = db.session.query(User).get(1)
            user.valid_email = False
            db.session.commit()
            fake_signer.loads.return_value = dict(fullname=user.fullname,
                                                  name=user.name,
                                                  email_addr=user.email_addr)
            self.app.get('/account/register/confirmation?key=valid-key')

            url_for.assert_called_with('account.newsletter_subscribe', next=None)

            newsletter.ask_user_to_subscribe.return_value = False
            self.app.get('/account/register/confirmation?key=valid-key')
            url_for.assert_called_with('home.home')

    @with_context
    @patch('pybossa.view.account.newsletter', autospec=True)
    @patch('pybossa.view.account.url_for')
    @patch('pybossa.view.account.signer')
    def test_newsletter_json(self, fake_signer, url_for, newsletter):
        """Test WEB confirm email shows newsletter or home with JSON."""
        newsletter.ask_user_to_subscribe.return_value = True
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'key'}):
            self.register()
            user = db.session.query(User).get(1)
            user.valid_email = True
            url = '/account/newsletter'
            res = self.app_get_json(url)
            data = json.loads(res.data)
            assert data.get('title') == 'Subscribe to our Newsletter', data
            assert data.get('template') == 'account/newsletter.html', data


            res = self.app_get_json(url + "?subscribe=True")
            data = json.loads(res.data)
            assert data.get('flash') == 'You are subscribed to our newsletter!', data
            assert data.get('status') == SUCCESS, data


    @with_context
    @patch('pybossa.view.account.signer')
    def test_register_confirmation_creates_new_account(self, fake_signer):
        """Test WEB register confirmation creates the new account"""
        fake_signer.loads.return_value = dict(fullname='FN', name='name',
                                              email_addr='email',
                                              password='password',
                                              consent=False)
        res = self.app.get('/account/register/confirmation?key=valid-key')

        user = db.session.query(User).filter_by(name='name').first()

        assert user is not None
        assert user.check_password('password')

    @with_context
    def test_04_signin_signout_json(self):
        """Test WEB sign in and sign out JSON works"""
        res = self.register()
        # Log out as the registration already logs in the user
        res = self.signout()

        res = self.signin(method="GET", content_type="application/json",
                          follow_redirects=False)
        data = json.loads(res.data)
        err_msg = "There should be a form with two keys email & password"
        csrf = data.get('csrf')
        assert data.get('title') == "Sign in", data
        assert 'email' in list(data.get('form').keys()), (err_msg, data)
        assert 'password' in list(data.get('form').keys()), (err_msg, data)

        res = self.signin(email='', content_type="application/json",
                          follow_redirects=False, csrf=csrf)

        data = json.loads(res.data)
        err_msg = "There should be errors in email"
        assert data.get('form').get('errors'), (err_msg, data)
        assert data.get('form').get('errors').get('email'), (err_msg, data)
        msg = "Please correct the errors"
        assert data.get('flash') == msg, (data, err_msg)
        res = self.signin(password='', content_type="application/json",
                          follow_redirects=False, csrf=csrf)
        data = json.loads(res.data)
        assert data.get('flash') == msg, (data, err_msg)
        msg = "You must provide a password"
        assert msg in data.get('form').get('errors').get('password'), (err_msg, data)

        res = self.signin(email='', password='',
                          content_type='application/json',
                          follow_redirects=False,
                          csrf=csrf)
        msg = "Please correct the errors"
        data = json.loads(res.data)
        err_msg = "There should be a flash message"
        assert data.get('flash') == msg, (err_msg, data)
        msg = "The e-mail is required"
        assert data.get('form').get('errors').get('email')[0] == msg, (msg, data)
        msg = "You must provide a password"
        assert data.get('form').get('errors').get('password')[0] == msg, (msg, data)


        # Non-existant user
        msg = "Ooops, we didn't find you in the system"
        res = self.signin(email='wrongemail', content_type="application/json",
                          follow_redirects=False, csrf=csrf)
        data = json.loads(res.data)
        assert msg in data.get('flash'), (msg, data)
        assert data.get('status') == INFO, (data)

        res = self.signin(email='wrongemail', password='wrongpassword')
        res = self.signin(email='wrongemail', password='wrongpassword',
                          content_type="application/json",
                          follow_redirects=False, csrf=csrf)
        data = json.loads(res.data)
        assert msg in data.get('flash'), (msg, data)
        assert data.get('status') == INFO, (data)

        # Real user but wrong password or username
        msg = "Ooops, Incorrect email/password"
        res = self.signin(password='wrongpassword',
                          content_type="application/json",
                          csrf=csrf,
                          follow_redirects=False)
        data = json.loads(res.data)
        assert msg in data.get('flash'), (msg, data)
        assert data.get('status') == ERROR, (data)

        res = self.signin(content_type="application/json",
                          csrf=csrf, follow_redirects=False)
        data = json.loads(res.data)
        msg = "Welcome back John Doe"
        assert data.get('flash') == msg, (msg, data)
        assert data.get('status') == SUCCESS, (msg, data)
        assert data.get('next') == '/', (msg, data)

        # TODO: add JSON support to profile page.
        # # Check profile page with several information chunks
        # res = self.profile()
        # assert self.html_title("Profile") in str(res.data), res
        # assert "John Doe" in str(res.data), res
        # assert "johndoe@example.com" in str(res.data), res

        # Log out
        res = self.signout(content_type="application/json",
                           follow_redirects=False)
        msg = "You are now signed out"
        data = json.loads(res.data)
        assert data.get('flash') == msg, (msg, data)
        assert data.get('status') == SUCCESS, data
        assert data.get('next') == '/', data

        # TODO: add json to profile public page
        # # Request profile as an anonymous user
        # # Check profile page with several information chunks
        # res = self.profile()
        # assert "John Doe" in str(res.data), res
        # assert "johndoe@example.com" not in str(res.data), res

        # Try to access protected areas like update
        res = self.app.get('/account/johndoe/update', follow_redirects=True,
                           content_type="application/json")
        # As a user must be signed in to access, the page the title will be the
        # redirection to log in
        assert self.html_title("Sign in") in str(res.data), res.data
        assert "Please sign in to access this page." in str(res.data), res.data

        # TODO: Add JSON to profile
        # res = self.signin(next='%2Faccount%2Fprofile',
        #                   content_type="application/json",
        #                   csrf=csrf)
        # assert self.html_title("Profile") in str(res.data), res
        # assert "Welcome back %s" % "John Doe" in str(res.data), res


    @with_context
    def test_04_signin_signout(self):
        """Test WEB sign in and sign out works"""
        res = self.register()
        # Log out as the registration already logs in the user
        res = self.signout()

        res = self.signin(method="GET")
        assert self.html_title("Sign in") in str(res.data), res.data
        assert "Sign in" in str(res.data), res.data

        res = self.signin(email='')
        assert "Please correct the errors" in str(res.data), res
        assert "The e-mail is required" in str(res.data), res

        res = self.signin(password='')
        assert "Please correct the errors" in str(res.data), res
        assert "You must provide a password" in str(res.data), res

        res = self.signin(email='', password='')
        assert "Please correct the errors" in str(res.data), res
        assert "The e-mail is required" in str(res.data), res
        assert "You must provide a password" in str(res.data), res

        # Non-existant user
        msg = "Ooops, we didn&#39;t find you in the system"
        res = self.signin(email='wrongemail')
        assert msg in str(res.data), res.data

        res = self.signin(email='wrongemail', password='wrongpassword')
        assert msg in str(res.data), res

        # Real user but wrong password or username
        msg = "Ooops, Incorrect email/password"
        res = self.signin(password='wrongpassword')
        assert msg in str(res.data), res

        res = self.signin()
        assert self.html_title() in str(res.data), res
        assert "Welcome back %s" % "John Doe" in str(res.data), res

        # Check profile page with several information chunks
        res = self.profile()
        assert self.html_title("Profile") in str(res.data), res
        assert "John Doe" in str(res.data), res
        assert "johndoe@example.com" in str(res.data), res

        # Log out
        res = self.signout()
        assert self.html_title() in str(res.data), res
        assert "You are now signed out" in str(res.data), res

        # Request profile as an anonymous user
        # Check profile page with several information chunks
        res = self.profile()
        assert "John Doe" in str(res.data), res
        assert "johndoe@example.com" not in str(res.data), res

        # Try to access protected areas like update
        res = self.app.get('/account/johndoe/update', follow_redirects=True)
        # As a user must be signed in to access, the page the title will be the
        # redirection to log in
        assert self.html_title("Sign in") in str(res.data), res.data
        assert "Please sign in to access this page." in str(res.data), res.data

        res = self.signin(next='%2Faccount%2Fprofile')
        assert self.html_title("Profile") in str(res.data), res
        assert "Welcome back %s" % "John Doe" in str(res.data), res


    @with_context
    def test_05_test_signout_json(self):
        """Test WEB signout works with json."""
        res = self.app.get('/account/signout',
                           content_type='application/json')
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        err_msg = "next URI is wrong in redirction"
        assert data['next'] == '/', err_msg
        err_msg = "success message missing"
        assert data['status'] == 'success', err_msg


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_profile_applications(self, mock):
        """Test WEB user profile project page works."""
        self.create()
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        self.new_project()
        url = '/account/%s/applications' % Fixtures.name
        res = self.app.get(url)
        assert "Projects" in str(res.data), res.data
        assert "Published" in str(res.data), res.data
        assert "Draft" in str(res.data), res.data
        assert Fixtures.project_name in str(res.data), res.data

        url = '/account/fakename/applications'
        res = self.app.get(url)
        assert res.status_code == 404, res.status_code

        url = '/account/%s/applications' % Fixtures.name2
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_profile_projects(self, mock):
        """Test WEB user profile project page works."""
        self.create()
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        self.new_project()
        url = '/account/%s/projects' % Fixtures.name
        res = self.app.get(url)
        assert "Projects" in str(res.data), res.data
        assert "Published" in str(res.data), res.data
        assert "Draft" in str(res.data), res.data
        assert Fixtures.project_name in str(res.data), res.data

        url = '/account/fakename/projects'
        res = self.app.get(url)
        assert res.status_code == 404, res.status_code

        url = '/account/%s/projects' % Fixtures.name2
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_profile_projects_json(self, mock):
        """Test WEB user profile project page works."""
        self.create()
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        self.new_project()
        url = '/account/%s/projects' % Fixtures.name
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert data['title'] == 'Projects', data
        assert data['template'] == 'account/projects.html', data
        assert 'projects_draft' in str(data), data
        assert 'projects_published' in str(data), data

        assert data['projects_draft'][0]['id'] == 2
        assert data['projects_published'][0]['id'] == 1
        assert data['projects_published'][0]['name'] == Fixtures.project_name

        url = '/account/fakename/projects'
        res = self.app.get(url)
        assert res.status_code == 404, res.status_code

        url = '/account/%s/projects' % Fixtures.name2
        res = self.app.get(url)
        assert res.status_code == 403, res.status_code


    @with_context
    def test_05_update_user_profile_json(self):
        """Test WEB update user profile JSON"""

        # Create an account and log in
        self.register()
        url = "/account/fake/update"
        res = self.app.get(url, content_type="application/json")
        data = json.loads(res.data)
        assert res.status_code == 404, res.status_code
        assert data.get('code') == 404, res.status_code

        # Update profile with new data
        res = self.update_profile(method="GET", content_type="application/json")
        data = json.loads(res.data)
        msg = "Update your profile: %s" % "John Doe"
        err_msg = "There should be a title"
        assert data['title'] == msg, err_msg
        err_msg = "There should be 3 forms"
        assert data['form'] is not None, err_msg
        assert data['password_form'] is not None, err_msg
        assert data['upload_form'] is not None, err_msg
        err_msg = "There should be a csrf token"
        assert data['form']['csrf'] is not None, err_msg
        assert data['password_form']['csrf'] is not None, err_msg
        assert data['upload_form']['csrf'] is not None, err_msg

        csrf = data['form']['csrf']

        res = self.update_profile(fullname="John Doe 2",
                                  email_addr="johndoe2@example",
                                  locale="en",
                                  content_type="application/json",
                                  csrf=csrf)
        data = json.loads(res.data)

        err_msg = "There should be errors"
        assert data['form']['errors'] is not None, err_msg
        assert data['form']['errors']['email_addr'] is not None, err_msg

        res = self.update_profile(fullname="John Doe 2",
                                  email_addr="johndoe2@example.com",
                                  locale="en",
                                  content_type="application/json",
                                  csrf=csrf)
        data = json.loads(res.data)
        title = "Update your profile: John Doe 2"
        assert data.get('status') == SUCCESS, res.data
        user = user_repo.get_by(email_addr='johndoe2@example.com')
        url = '/account/%s/update' % user.name
        assert data.get('next') == url, res.data
        flash = "Your profile has been updated!"
        err_msg = "There should be a flash message"
        assert data.get('flash') == flash, (data, err_msg)
        err_msg = "It should return the same updated data"
        assert "John Doe 2" == user.fullname, user.fullname
        assert "johndoe" == user.name, err_msg
        assert "johndoe2@example.com" == user.email_addr, err_msg
        assert user.subscribed is False, err_msg

        # Updating the username field forces the user to re-log in
        res = self.update_profile(fullname="John Doe 2",
                                  email_addr="johndoe2@example.com",
                                  locale="en",
                                  new_name="johndoe2",
                                  content_type='application/json',
                                  csrf=csrf)
        data = json.loads(res.data)
        err_msg = "Update should work"
        assert data.get('status') == SUCCESS, (err_msg, data)
        url = "/account/johndoe2/update"
        assert data.get('next') == url, (err_msg, data)
        res = self.app.get(url, follow_redirects=False,
                           content_type='application/json')
        assert res.status_code == 302, res.status_code
        assert "/account/signin" in str(res.data), res.data

        res = self.signin(method="POST", email="johndoe2@example.com",
                          password="p4ssw0rd",
                          next="%2Faccount%2Fprofile")
        assert "Welcome back John Doe 2" in str(res.data), res.data
        assert "John Doe 2" in str(res.data), res
        assert "johndoe2" in str(res.data), res
        assert "johndoe2@example.com" in str(res.data), res

        res = self.app.get('/', follow_redirects=False)
        assert "::logged-in::johndoe2" in str(res.data), res.data


        res = self.signout(follow_redirects=False,
                           content_type="application/json")

        data = json.loads(res.data)
        err_msg = "User should be logged out"
        assert self.check_cookie(res, 'remember_token') == "", err_msg
        assert data.get('status') == SUCCESS, (err_msg, data)
        assert data.get('next') == '/', (err_msg, data)
        assert "You are now signed out" == data.get('flash'), (err_msg, data)
        res = self.app.get('/', follow_redirects=False)
        assert "::logged-in::johndoe2" not in str(res.data), err_msg

        # A user must be signed in to access the update page, the page
        # the title will be the redirection to log in
        res = self.update_profile(method="GET", follow_redirects=False,
                                  content_type="application/json")
        err_msg = "User should be requested to log in"
        assert res.status_code == 302, err_msg
        assert "/account/signin" in str(res.data), err_msg

        self.register(fullname="new", name="new")
        url = "/account/johndoe2/update"
        res = self.app.get(url, content_type="application/json")
        data = json.loads(res.data)
        assert res.status_code == 403
        assert data.get('code') == 403
        assert data.get('description') == FORBIDDEN, data


    @with_context
    def test_05_update_user_profile(self):
        """Test WEB update user profile"""

        # Create an account and log in
        self.register()
        url = "/account/fake/update"
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.status_code

        # Update profile with new data
        res = self.update_profile(method="GET")
        msg = "Update your profile: %s" % "John Doe"
        assert self.html_title(msg) in str(res.data), res.data
        msg = 'input id="id" name="id" type="hidden" value="1"'
        assert msg in str(res.data), res
        assert "John Doe" in str(res.data), res
        assert "Save the changes" in str(res.data), res

        res = self.update_profile(fullname="John Doe 2",
                                  email_addr="johndoe2@example",
                                  locale="en")
        assert "Please correct the errors" in str(res.data), res.data

        res = self.update_profile(fullname="John Doe 2",
                                  email_addr="johndoe2@example.com",
                                  locale="en")
        title = "Update your profile: John Doe 2"
        assert self.html_title(title) in str(res.data), res.data
        user = user_repo.get_by(email_addr='johndoe2@example.com')
        assert "Your profile has been updated!" in str(res.data), res.data
        assert "John Doe 2" in str(res.data), res
        assert "John Doe 2" == user.fullname, user.fullname
        assert "johndoe" in str(res.data), res
        assert "johndoe" == user.name, user.name
        assert "johndoe2@example.com" in str(res.data), res
        assert "johndoe2@example.com" == user.email_addr, user.email_addr
        assert user.subscribed is False, user.subscribed

        # Updating the username field forces the user to re-log in
        res = self.update_profile(fullname="John Doe 2",
                                  email_addr="johndoe2@example.com",
                                  locale="en",
                                  new_name="johndoe2")
        assert "Your profile has been updated!" in str(res.data), res
        assert "Please sign in" in str(res.data), res.data

        res = self.signin(method="POST", email="johndoe2@example.com",
                          password="p4ssw0rd",
                          next="%2Faccount%2Fprofile")
        assert "Welcome back John Doe 2" in str(res.data), res.data
        assert "John Doe 2" in str(res.data), res
        assert "johndoe2" in str(res.data), res
        assert "johndoe2@example.com" in str(res.data), res

        res = self.signout()
        assert self.html_title() in str(res.data), res
        assert "You are now signed out" in str(res.data), res

        # A user must be signed in to access the update page, the page
        # the title will be the redirection to log in
        res = self.update_profile(method="GET")
        assert self.html_title("Sign in") in str(res.data), res
        assert "Please sign in to access this page." in str(res.data), res

        # A user must be signed in to access the update page, the page
        # the title will be the redirection to log in
        res = self.update_profile()
        assert self.html_title("Sign in") in str(res.data), res
        assert "Please sign in to access this page." in str(res.data), res

        self.register(fullname="new", name="new")
        url = "/account/johndoe2/update"
        res = self.app.get(url)
        assert res.status_code == 403

    @with_context
    def test_05a_get_nonexistant_app(self):
        """Test WEB get not existant project should return 404"""
        res = self.app.get('/project/nonapp', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    @with_context
    def test_05b_get_nonexistant_app_newtask(self):
        """Test WEB get non existant project newtask should return 404"""
        res = self.app.get('/project/noapp/presenter', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        res = self.app.get('/project/noapp/newtask', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    @with_context
    def test_05c_get_nonexistant_app_tutorial(self):
        """Test WEB get non existant project tutorial should return 404"""
        res = self.app.get('/project/noapp/tutorial', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        res = self.app_get_json('/project/noapp/tutorial')
        assert res.status == '404 NOT FOUND', res.status

    @with_context
    def test_05d_get_nonexistant_app_delete(self):
        """Test WEB get non existant project delete should return 404"""
        self.register()
        # GET
        res = self.app.get('/project/noapp/delete', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.data
        # POST
        res = self.delete_project(short_name="noapp")
        assert res.status == '404 NOT FOUND', res.status

    @with_context
    def test_delete_project(self):
        """Test WEB JSON delete project."""
        owner = UserFactory.create()
        user = UserFactory.create()
        project = ProjectFactory.create(short_name="algo", owner=owner)
        # As anon
        url = '/project/%s/delete' % project.short_name
        res = self.app_get_json(url, follow_redirects=True)
        assert 'signin' in str(res.data), res.data

        url = '/project/%s/delete' % project.short_name
        res = self.app_post_json(url)
        assert 'signin' in str(res.data), res.data

        # As not owner
        url = '/project/%s/delete?api_key=%s' % (project.short_name, user.api_key)
        res = self.app_get_json(url, follow_redirects=True)
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['code'] == 403, data

        url = '/project/%s/delete?api_key=%s' % (project.short_name, user.api_key)
        res = self.app_post_json(url, follow_redirects=True)
        data = json.loads(res.data)
        assert res.status_code == 403, data
        assert data['code'] == 403, data

        # As owner
        url = '/project/%s/delete?api_key=%s' % (project.short_name, owner.api_key)
        res = self.app_get_json(url, follow_redirects=True)
        data = json.loads(res.data)
        assert res.status_code == 200, data
        assert data['project']['name'] == project.name, data

        res = self.app_post_json(url)
        data = json.loads(res.data)
        assert data['status'] == SUCCESS, data
        p = db.session.query(Project).get(project.id)
        assert p is None

    @with_context
    def test_05d_get_nonexistant_project_update(self):
        """Test WEB get non existant project update should return 404"""
        self.register()
        # GET
        res = self.app.get('/project/noapp/update', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # POST
        res = self.update_project(short_name="noapp")
        assert res.status == '404 NOT FOUND', res.status

    @with_context
    def test_project_upload_thumbnail(self):
        """Test WEB Project upload thumbnail."""
        import io
        owner = UserFactory.create()
        project = ProjectFactory.create(owner=owner)
        url = '/project/%s/update?api_key=%s' % (project.short_name,
                                                 owner.api_key)
        avatar = (io.BytesIO(b'test'), 'test_file.jpg')
        payload = dict(btn='Upload', avatar=avatar,
                       id=project.id, x1=0, y1=0,
                       x2=100, y2=100)
        res = self.app.post(url, follow_redirects=True,
                            content_type="multipart/form-data", data=payload)
        assert res.status_code == 200
        p = project_repo.get(project.id)
        assert p.info['thumbnail'] is not None
        assert p.info['container'] is not None
        thumbnail_url = 'https://localhost/uploads/%s/%s' % (p.info['container'], p.info['thumbnail'])
        assert p.info['thumbnail_url'] == thumbnail_url

    @with_context
    def test_account_upload_avatar(self):
        """Test WEB Account upload avatar."""
        import io
        owner = UserFactory.create()
        url = '/account/%s/update?api_key=%s' % (owner.name,
                                                 owner.api_key)
        avatar = (io.BytesIO(b'test'), 'test_file.jpg')
        payload = dict(btn='Upload', avatar=avatar,
                       id=owner.id, x1=0, y1=0,
                       x2=100, y2=100)
        res = self.app.post(url, follow_redirects=True,
                            content_type="multipart/form-data", data=payload)
        assert res.status_code == 200
        u = user_repo.get(owner.id)
        assert u.info['avatar'] is not None
        assert u.info['container'] is not None
        avatar_url = 'https://localhost/uploads/%s/%s' % (u.info['container'], u.info['avatar'])
        assert u.info['avatar_url'] == avatar_url, u.info['avatar_url']

    @with_context
    def test_05d_get_nonexistant_project_update_json(self):
        """Test WEB JSON get non existant project update should return 404"""
        self.register()
        # GET
        url = '/project/noapp/update'
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert res.status == '404 NOT FOUND', res.status
        assert data['code'] == 404, data
        # POST
        res = self.app_post_json(url, data=dict())
        assert res.status == '404 NOT FOUND', res.status
        data = json.loads(res.data)
        assert data['code'] == 404, data

    @with_context
    def test_get_project_json(self):
        """Test WEB JSON get project by short name."""
        project = ProjectFactory.create()
        url = '/project/%s/' % project.short_name
        res = self.app_get_json(url)

        data = json.loads(res.data)['project']

        assert 'id' in list(data.keys()), list(data.keys())
        assert 'description' in list(data.keys()), list(data.keys())
        assert 'info' in list(data.keys()), list(data.keys())
        assert 'long_description' in list(data.keys()), list(data.keys())
        assert 'n_tasks' in list(data.keys()), list(data.keys())
        assert 'n_volunteers' in list(data.keys()), list(data.keys())
        assert 'name' in list(data.keys()), list(data.keys())
        assert 'overall_progress' in list(data.keys()), list(data.keys())
        assert 'short_name' in list(data.keys()), list(data.keys())
        assert 'created' in list(data.keys()), list(data.keys())
        assert 'long_description' in list(data.keys()), list(data.keys())
        assert 'last_activity' in list(data.keys()), list(data.keys())
        assert 'last_activity_raw' in list(data.keys()), list(data.keys())
        assert 'n_task_runs' in list(data.keys()), list(data.keys())
        assert 'n_results' in list(data.keys()), list(data.keys())
        assert 'owner' in list(data.keys()), list(data.keys())
        assert 'updated' in list(data.keys()), list(data.keys())
        assert 'featured' in list(data.keys()), list(data.keys())
        assert 'owner_id' in list(data.keys()), list(data.keys())
        assert 'n_completed_tasks' in list(data.keys()), list(data.keys())
        assert 'n_blogposts' in list(data.keys()), list(data.keys())

    @with_context
    def test_update_project_json_as_user(self):
        """Test WEB JSON update project as user."""
        admin = UserFactory.create()
        owner = UserFactory.create()
        user = UserFactory.create()

        project = ProjectFactory.create(owner=owner)

        url = '/project/%s/update?api_key=%s' % (project.short_name, user.api_key)

        res = self.app_get_json(url)
        data = json.loads(res.data)

        assert data['code'] == 403, data

        old_data = dict()

        old_data['description'] = 'foobar'

        res = self.app_post_json(url, data=old_data)
        data = json.loads(res.data)

        assert data['code'] == 403, data

    @with_context
    @patch('pybossa.view.projects.cached_projects.clean_project')
    def test_update_project_json_as_admin(self, cache_mock):
        """Test WEB JSON update project as admin."""
        admin = UserFactory.create()
        owner = UserFactory.create()
        user = UserFactory.create()

        project = ProjectFactory.create(owner=owner)

        url = '/project/%s/update?api_key=%s' % (project.short_name, admin.api_key)

        res = self.app_get_json(url)
        data = json.loads(res.data)

        assert data['form']['csrf'] is not None, data
        assert data['upload_form']['csrf'] is not None, data

        old_data = data['form']
        del old_data['csrf']
        del old_data['errors']

        old_data['description'] = 'foobar'

        res = self.app_post_json(url, data=old_data)
        data = json.loads(res.data)

        assert data['status'] == SUCCESS, data

        u_project = project_repo.get(project.id)
        assert u_project.description == 'foobar', u_project
        cache_mock.assert_called_with(project.id)


    @with_context
    def test_update_project_json_as_owner(self):
        """Test WEB JSON update project."""
        admin = UserFactory.create()
        owner = UserFactory.create()
        user = UserFactory.create()

        project = ProjectFactory.create(owner=owner)

        url = '/project/%s/update?api_key=%s' % (project.short_name, owner.api_key)

        res = self.app_get_json(url)
        data = json.loads(res.data)

        assert data['form']['csrf'] is not None, data
        assert data['upload_form']['csrf'] is not None, data

        old_data = data['form']
        del old_data['csrf']
        del old_data['errors']

        old_data['description'] = 'foobar'

        res = self.app_post_json(url, data=old_data)
        data = json.loads(res.data)

        assert data['status'] == SUCCESS, data

        u_project = project_repo.get(project.id)
        assert u_project.description == 'foobar', u_project


    @with_context
    def test_update_project_json_as_owner(self):
        """Test WEB JSON update project."""
        admin = UserFactory.create()
        owner = UserFactory.create()
        user = UserFactory.create()

        project = ProjectFactory.create(owner=owner)

        url = '/project/%s/update?api_key=%s' % (project.short_name, owner.api_key)

        res = self.app_get_json(url)
        data = json.loads(res.data)

        assert data['form']['csrf'] is not None, data
        assert data['upload_form']['csrf'] is not None, data

        old_data = data['form']
        del old_data['csrf']
        del old_data['errors']

        old_data['description'] = 'foobar'

        res = self.app_post_json(url, data=old_data)
        data = json.loads(res.data)

        assert data['status'] == SUCCESS, data



    @with_context
    def test_05d_get_nonexistant_app_import(self):
        """Test WEB get non existant project import should return 404"""
        self.register()
        # GET
        res = self.app.get('/project/noapp/import', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # POST
        res = self.app.post('/project/noapp/import', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    @with_context
    def test_05d_get_nonexistant_app_task(self):
        """Test WEB get non existant project task should return 404"""
        res = self.app.get('/project/noapp/task', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Pagination
        res = self.app.get('/project/noapp/task/25', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    @with_context
    def test_05d_get_nonexistant_app_task_json(self):
        """Test WEB get non existant project task should return 404"""
        res = self.app_get_json('/project/noapp/task')
        assert res.status == '404 NOT FOUND', res.status
        # Pagination
        res = self.app_get_json('/project/noapp/task/25')
        assert res.status == '404 NOT FOUND', res.status


    @with_context
    def test_05d_get_nonexistant_app_results_json(self):
        """Test WEB get non existant project results json should return 404"""
        res = self.app.get('/project/noapp/24/results.json', follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

    @with_context
    def test_06_applications_without_apps(self):
        """Test WEB projects index without projects works"""
        # Check first without apps
        self.create_categories()
        res = self.app.get('/project/category/featured', follow_redirects=True)
        assert "Projects" in str(res.data), res.data
        assert Fixtures.cat_1 in str(res.data), res.data

    @with_context
    def test_06_applications_2(self):
        """Test WEB projects index with projects"""
        self.create()

        res = self.app.get('/project/category/featured', follow_redirects=True)
        assert self.html_title("Projects") in str(res.data), res.data
        assert "Projects" in str(res.data), res.data
        assert Fixtures.project_short_name in str(res.data), res.data

    @with_context
    def test_06_featured_project_json(self):
        """Test WEB JSON projects index shows featured projects in all the pages works"""
        self.create()

        project = db.session.query(Project).get(1)
        project.featured = True
        db.session.add(project)
        db.session.commit()
        # Update one task to have more answers than expected
        task = db.session.query(Task).get(1)
        task.n_answers = 1
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).get(1)
        cat = db.session.query(Category).get(1)
        url = '/project/category/featured/'
        res = self.app_get_json(url, follow_redirects=True)
        data = json.loads(res.data)
        assert 'pagination' in list(data.keys()), data
        assert 'active_cat' in list(data.keys()), data
        assert 'categories' in list(data.keys()), data
        assert 'projects' in list(data.keys()), data
        assert data['pagination']['next'] is False, data
        assert data['pagination']['prev'] is False, data
        assert data['pagination']['total'] == 1, data
        assert data['active_cat']['name'] == 'Featured', data
        assert len(data['projects']) == 1, data
        assert data['projects'][0]['id'] == project.id, data


    @with_context
    def test_06_featured_projects(self):
        """Test WEB projects index shows featured projects in all the pages works"""
        self.create()

        project = db.session.query(Project).get(1)
        project.featured = True
        db.session.add(project)
        db.session.commit()

        res = self.app.get('/project/category/featured', follow_redirects=True)
        assert self.html_title("Projects") in str(res.data), res.data
        assert "Projects" in str(res.data), res.data
        assert '/project/test-app' in str(res.data), res.data
        assert 'My New Project' in str(res.data), res.data

        # Update one task to have more answers than expected
        task = db.session.query(Task).get(1)
        task.n_answers = 1
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).get(1)
        cat = db.session.query(Category).get(1)
        url = '/project/category/featured/'
        res = self.app.get(url, follow_redirects=True)
        assert 'Featured Projects' in str(res.data), res.data

    @with_context
    @patch('pybossa.ckan.requests.get')
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_10_get_application(self, Mock, mock2):
        """Test WEB project URL/<short_name> works"""
        # Sign in and create a project
        html_request = FakeResponse(text=json.dumps(self.pkg_json_not_found),
                                    status_code=200,
                                    headers={'content-type': 'application/json'},
                                    encoding='utf-8')
        Mock.return_value = html_request
        self.register()
        res = self.new_project()
        project = db.session.query(Project).first()
        project.published = True
        db.session.commit()
        TaskFactory.create(project=project)

        res = self.app.get('/project/sampleapp', follow_redirects=True)
        assert_raises(ValueError, json.loads, res.data)
        msg = "Project: Sample Project"
        assert self.html_title(msg) in str(res.data), res
        err_msg = "There should be a contribute button"
        assert "Start Contributing Now!" in str(res.data), err_msg

        res = self.app.get('/project/sampleapp/settings', follow_redirects=True)
        assert_raises(ValueError, json.loads, res.data)
        assert res.status == '200 OK', res.status
        self.signout()

        # Now as an anonymous user
        res = self.app.get('/project/sampleapp', follow_redirects=True)
        assert_raises(ValueError, json.loads, res.data)
        assert self.html_title("Project: Sample Project") in str(res.data), res
        assert "Start Contributing Now!" in str(res.data), err_msg
        res = self.app.get('/project/sampleapp/settings', follow_redirects=True)
        assert res.status == '200 OK', res.status
        err_msg = "Anonymous user should be redirected to sign in page"
        assert "Please sign in to access this page" in str(res.data), err_msg

        # Now with a different user
        self.register(fullname="Perico Palotes", name="perico")
        res = self.app.get('/project/sampleapp', follow_redirects=True)
        assert_raises(ValueError, json.loads, res.data)
        assert self.html_title("Project: Sample Project") in str(res.data), res
        assert "Start Contributing Now!" in str(res.data), err_msg
        res = self.app.get('/project/sampleapp/settings')
        assert res.status == '403 FORBIDDEN', res.status

    @with_context
    @patch('pybossa.ckan.requests.get')
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_10_get_application_json(self, Mock, mock2):
        """Test WEB project URL/<short_name> works JSON"""
        # Sign in and create a project
        html_request = FakeResponse(text=json.dumps(self.pkg_json_not_found),
                                    status_code=200,
                                    headers={'content-type': 'application/json'},
                                    encoding='utf-8')
        Mock.return_value = html_request
        self.register()
        res = self.new_project()
        project = db.session.query(Project).first()
        project.published = True
        db.session.commit()
        TaskFactory.create(project=project)

        res = self.app_get_json('/project/sampleapp/')
        data = json.loads(res.data)
        assert 'last_activity' in str(data), res.data
        assert 'n_completed_tasks' in str(data), res.data
        assert 'n_task_runs' in str(data), res.data
        assert 'n_tasks' in str(data), res.data
        assert 'n_volunteers' in str(data), res.data
        assert 'overall_progress' in str(data), res.data
        assert 'owner' in str(data), res.data
        assert 'pro_features' in str(data), res.data
        assert 'project' in str(data), res.data
        assert 'template' in str(data), res.data
        assert 'title' in str(data), res.data
        # private information
        assert 'api_key' in data['owner'], res.data
        assert 'email_addr' in data['owner'], res.data
        assert 'secret_key' in data['project'], res.data
        assert 'owner_id' in data['project'], res.data

        res = self.app_get_json('/project/sampleapp/settings')
        assert res.status == '200 OK', res.status
        data = json.loads(res.data)
        assert 'last_activity' in str(data), res.data
        assert 'n_completed_tasks' in str(data), res.data
        assert 'n_task_runs' in str(data), res.data
        assert 'n_tasks' in str(data), res.data
        assert 'n_volunteers' in str(data), res.data
        assert 'overall_progress' in str(data), res.data
        assert 'owner' in str(data), res.data
        assert 'pro_features' in str(data), res.data
        assert 'project' in str(data), res.data
        assert 'template' in str(data), res.data
        assert 'title' in str(data), res.data
        # private information
        assert 'api_key' in data['owner'], res.data
        assert 'email_addr' in data['owner'], res.data
        assert 'secret_key' in data['project'], res.data
        assert 'owner_id' in data['project'], res.data

        self.signout()

        # Now as an anonymous user
        res = self.app_get_json('/project/sampleapp/')
        data = json.loads(res.data)
        assert 'last_activity' in str(data), res.data
        assert 'n_completed_tasks' in str(data), res.data
        assert 'n_task_runs' in str(data), res.data
        assert 'n_tasks' in str(data), res.data
        assert 'n_volunteers' in str(data), res.data
        assert 'overall_progress' in str(data), res.data
        assert 'owner' in str(data), res.data
        assert 'pro_features' in str(data), res.data
        assert 'project' in str(data), res.data
        assert 'template' in str(data), res.data
        assert 'title' in str(data), res.data
        # private information
        assert 'api_key' not in data['owner'], res.data
        assert 'email_addr' not in data['owner'], res.data
        assert 'secret_key' not in data['project'], res.data

        res = self.app_get_json('/project/sampleapp/settings')
        assert res.status == '302 FOUND', res.status

        # Now with a different user
        self.register(fullname="Perico Palotes", name="perico")
        res = self.app_get_json('/project/sampleapp/')
        data = json.loads(res.data)
        assert 'last_activity' in str(data), res.data
        assert 'n_completed_tasks' in str(data), res.data
        assert 'n_task_runs' in str(data), res.data
        assert 'n_tasks' in str(data), res.data
        assert 'n_volunteers' in str(data), res.data
        assert 'overall_progress' in str(data), res.data
        assert 'owner' in str(data), res.data
        assert 'pro_features' in str(data), res.data
        assert 'project' in str(data), res.data
        assert 'template' in str(data), res.data
        assert 'title' in str(data), res.data
        # private information
        assert 'api_key' not in data['owner'], res.data
        assert 'email_addr' not in data['owner'], res.data
        assert 'secret_key' not in data['project'], res.data

        res = self.app_get_json('/project/sampleapp/settings')
        assert res.status == '403 FORBIDDEN', res.status

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_10b_application_long_description_allows_markdown(self, mock):
        """Test WEB long description markdown is supported"""
        markdown_description = 'Markdown\n======='
        self.register()
        self.new_project(long_description=markdown_description)

        res = self.app.get('/project/sampleapp', follow_redirects=True)
        data = res.data
        assert '<h1>Markdown</h1>' in str(data), 'Markdown text not being rendered!'

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_11_create_application(self, mock):
        """Test WEB create a project works"""
        # Create a project as an anonymous user
        res = self.new_project(method="GET")
        assert self.html_title("Sign in") in str(res.data), res
        assert "Please sign in to access this page" in str(res.data), res

        res = self.new_project()
        assert self.html_title("Sign in") in str(res.data), res.data
        assert "Please sign in to access this page." in str(res.data), res.data

        # Sign in and create a project
        res = self.register()

        res = self.new_project(method="GET")
        assert self.html_title("Create a Project") in str(res.data), res
        assert "Create the project" in str(res.data), res

        res = self.new_project(long_description='My Description')
        assert "Sample Project" in str(res.data)
        assert "Project created!" in str(res.data), res

        project = db.session.query(Project).first()
        assert project.name == 'Sample Project', 'Different names %s' % project.name
        assert project.short_name == 'sampleapp', \
            'Different names %s' % project.short_name

        assert project.long_description == 'My Description', \
            "Long desc should be the same: %s" % project.long_description

        assert project.category is not None, \
            "A project should have a category after being created"

    @with_context
    def test_description_is_generated_only_if_not_provided(self):
        """Test WEB when when creating a project and a description is provided,
        then it is not generated from the long_description"""
        self.register()
        res = self.new_project(long_description="a" * 300, description='b')

        project = db.session.query(Project).first()
        assert project.description == 'b', project.description

    @with_context
    def test_description_is_generated_from_long_desc(self):
        """Test WEB when creating a project, the description field is
        automatically filled in by truncating the long_description"""
        self.register()
        res = self.new_project(long_description="Hello", description='')

        project = db.session.query(Project).first()
        assert project.description == "Hello", project.description

    @with_context
    def test_description_is_generated_from_long_desc_formats(self):
        """Test WEB when when creating a project, the description generated
        from the long_description is only text (no html, no markdown)"""
        self.register()
        res = self.new_project(long_description="## Hello", description='')

        project = db.session.query(Project).first()
        assert '##' not in project.description, project.description
        assert '<h2>' not in project.description, project.description

    @with_context
    def test_description_is_generated_from_long_desc_truncates(self):
        """Test WEB when when creating a project, the description generated
        from the long_description is truncated to 255 chars"""
        self.register()
        res = self.new_project(long_description="a" * 300, description='')

        project = db.session.query(Project).first()
        assert len(project.description) == 255, len(project.description)
        assert project.description[-3:] == '...'

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_11_a_create_application_errors(self, mock):
        """Test WEB create a project issues the errors"""
        self.register()
        # Required fields checks
        # Issue the error for the project.name
        res = self.new_project(name="")
        err_msg = "A project must have a name"
        assert "This field is required" in str(res.data), err_msg

        # Issue the error for the project.short_name
        res = self.new_project(short_name="")
        err_msg = "A project must have a short_name"
        assert "This field is required" in str(res.data), err_msg

        # Issue the error for the project.description
        res = self.new_project(long_description="")
        err_msg = "A project must have a description"
        assert "This field is required" in str(res.data), err_msg

        # Issue the error for the project.short_name
        res = self.new_project(short_name='$#/|')
        err_msg = "A project must have a short_name without |/$# chars"
        assert 'space symbols are forbidden' in str(res.data), err_msg

        # Now Unique checks
        self.new_project()
        res = self.new_project()
        err_msg = "There should be a Unique field"
        assert "Name is already taken" in str(res.data), err_msg
        assert "Short Name is already taken" in str(res.data), err_msg

    @with_context
    @patch('pybossa.ckan.requests.get')
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    @patch('pybossa.forms.validator.requests.get')
    def test_12_update_project(self, Mock, mock, mock_webhook):
        """Test WEB update project works"""
        html_request = FakeResponse(text=json.dumps(self.pkg_json_not_found),
                                    status_code=200,
                                    headers={'content-type': 'application/json'},
                                    encoding='utf-8')
        Mock.return_value = html_request
        mock_webhook.return_value = html_request

        self.register()
        self.new_project()

        # Get the Update Project web page
        res = self.update_project(method="GET")
        msg = "Project: Sample Project &middot; Update"
        assert self.html_title(msg) in str(res.data), res
        msg = 'input id="id" name="id" type="hidden" value="1"'
        assert msg in str(res.data), res
        assert "Save the changes" in str(res.data), res

        # Check form validation
        res = self.update_project(new_name="",
                                  new_short_name="",
                                  new_description="New description",
                                  new_long_description='New long desc')
        assert "Please correct the errors" in str(res.data), res.data

        # Update the project
        res = self.update_project(new_name="New Sample Project",
                                  new_short_name="newshortname",
                                  new_description="New description",
                                  new_long_description='New long desc')
        project = db.session.query(Project).first()
        assert "Project updated!" in str(res.data), res.data
        err_msg = "Project name not updated %s" % project.name
        assert project.name == "New Sample Project", err_msg
        err_msg = "Project short name not updated %s" % project.short_name
        assert project.short_name == "newshortname", err_msg
        err_msg = "Project description not updated %s" % project.description
        assert project.description == "New description", err_msg
        err_msg = "Project long description not updated %s" % project.long_description
        assert project.long_description == "New long desc", err_msg

    @with_context
    @patch('pybossa.forms.validator.requests.get')
    def test_webhook_to_project(self, mock):
        """Test WEB update sets a webhook for the project"""
        html_request = FakeResponse(text=json.dumps(self.pkg_json_not_found),
                                    status_code=200,
                                    headers={'content-type': 'application/json'},
                                    encoding='utf-8')
        mock.return_value = html_request

        self.register()
        owner = db.session.query(User).first()
        project = ProjectFactory.create(owner=owner)

        new_webhook = 'http://mynewserver.com/'

        self.update_project(id=project.id, short_name=project.short_name,
                            new_webhook=new_webhook)

        err_msg = "There should be an updated webhook url."
        assert project.webhook == new_webhook, err_msg

    @with_context
    @patch('pybossa.forms.validator.requests.get')
    def test_webhook_to_project_fails(self, mock):
        """Test WEB update does not set a webhook for the project"""
        html_request = FakeResponse(text=json.dumps(self.pkg_json_not_found),
                                    status_code=404,
                                    headers={'content-type': 'application/json'},
                                    encoding='utf-8')
        mock.return_value = html_request

        self.register()
        owner = db.session.query(User).first()
        project = ProjectFactory.create(owner=owner)

        new_webhook = 'http://mynewserver.com/'

        self.update_project(id=project.id, short_name=project.short_name,
                            new_webhook=new_webhook)

        err_msg = "There should not be an updated webhook url."
        assert project.webhook != new_webhook, err_msg

    @with_context
    @patch('pybossa.forms.validator.requests.get')
    def test_webhook_to_project_conn_err(self, mock):
        """Test WEB update does not set a webhook for the project"""
        from requests.exceptions import ConnectionError
        mock.side_effect = ConnectionError

        self.register()
        owner = db.session.query(User).first()
        project = ProjectFactory.create(owner=owner)

        new_webhook = 'http://mynewserver.com/'

        res = self.update_project(id=project.id, short_name=project.short_name,
                                  new_webhook=new_webhook)

        err_msg = "There should not be an updated webhook url."
        assert project.webhook != new_webhook, err_msg

    @with_context
    @patch('pybossa.forms.validator.requests.get')
    def test_add_password_to_project(self, mock_webhook):
        """Test WEB update sets a password for the project"""
        html_request = FakeResponse(text=json.dumps(self.pkg_json_not_found),
                                    status_code=200,
                                    headers={'content-type': 'application/json'},
                                    encoding='utf-8')
        mock_webhook.return_value = html_request
        self.register()
        owner = db.session.query(User).first()
        project = ProjectFactory.create(owner=owner)

        self.update_project(id=project.id, short_name=project.short_name,
                            new_protect='true', new_password='mysecret')

        assert project.needs_password(), 'Password not set'

    @with_context
    @patch('pybossa.forms.validator.requests.get')
    def test_remove_password_from_project(self, mock_webhook):
        """Test WEB update removes the password of the project"""
        html_request = FakeResponse(text=json.dumps(self.pkg_json_not_found),
                                    status_code=200,
                                    headers={'content-type': 'application/json'},
                                    encoding='utf-8')
        mock_webhook.return_value = html_request
        self.register()
        owner = db.session.query(User).first()
        project = ProjectFactory.create(info={'passwd_hash': 'mysecret'}, owner=owner)

        self.update_project(id=project.id, short_name=project.short_name,
                            new_protect='false', new_password='')

        assert not project.needs_password(), 'Password not deleted'

    @with_context
    @patch('pybossa.forms.validator.requests.get')
    def test_update_project_errors(self, mock_webhook):
        """Test WEB update form validation issues the errors"""
        self.register()
        self.new_project()
        html_request = FakeResponse(text=json.dumps(self.pkg_json_not_found),
                                    status_code=200,
                                    headers={'content-type': 'application/json'},
                                    encoding='utf-8')

        mock_webhook.return_value = html_request

        res = self.update_project(new_name="")
        assert "This field is required" in str(res.data)

        res = self.update_project(new_short_name="")
        assert "This field is required" in str(res.data)

        res = self.update_project(new_description="")
        assert "You must provide a description." in str(res.data)

        res = self.update_project(new_description="a" * 256)
        assert "Field cannot be longer than 255 characters." in str(res.data)

        res = self.update_project(new_long_description="")
        assert "This field is required"  not in str(res.data)

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_14_delete_application(self, mock):
        """Test WEB delete project works"""
        self.create()
        self.register()
        self.new_project()
        res = self.delete_project(method="GET")
        msg = "Project: Sample Project &middot; Delete"
        assert self.html_title(msg) in str(res.data), res
        assert "No, do not delete it" in str(res.data), res

        project = db.session.query(Project).filter_by(short_name='sampleapp').first()
        res = self.delete_project(method="GET")
        msg = "Project: Sample Project &middot; Delete"
        assert self.html_title(msg) in str(res.data), res
        assert "No, do not delete it" in str(res.data), res

        res = self.delete_project()
        assert "Project deleted!" in str(res.data), res

        self.signin(email=Fixtures.email_addr2, password=Fixtures.password)
        res = self.delete_project(short_name=Fixtures.project_short_name)
        assert res.status_code == 403, res.status_code

    @with_context
    @patch('pybossa.repositories.project_repository.uploader')
    def test_delete_project_deletes_task_zip_files_too(self, uploader):
        """Test WEB delete project also deletes zip files for task and taskruns"""
        Fixtures.create()
        self.signin(email='tester@tester.com', password='tester')
        res = self.app.post('/project/test-app/delete', follow_redirects=True)
        expected = [call('1_test-app_task_json.zip', 'user_2'),
                    call('1_test-app_task_csv.zip', 'user_2'),
                    call('1_test-app_task_run_json.zip', 'user_2'),
                    call('1_test-app_task_run_csv.zip', 'user_2')]
        assert uploader.delete_file.call_args_list == expected

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_16_task_status_completed(self, mock):
        """Test WEB Task Status Completed works"""
        self.register()
        self.new_project()

        project = db.session.query(Project).first()
        # We use a string here to check that it works too
        project.published = True
        task = Task(project_id=project.id, n_answers=10)
        db.session.add(task)
        db.session.commit()

        res = self.app.get('project/%s/tasks/browse' % (project.short_name),
                           follow_redirects=True)
        dom = BeautifulSoup(res.data)
        assert "Sample Project" in str(res.data), res.data
        assert '0 of 10' in str(res.data), res.data
        err_msg = "Download button should be disabled"
        assert dom.find(id='nothingtodownload') is not None, err_msg

        for i in range(5):
            task_run = TaskRun(project_id=project.id, task_id=1,
                               info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()
            self.app.get('api/project/%s/newtask' % project.id)

        res = self.app.get('project/%s/tasks/browse' % (project.short_name),
                           follow_redirects=True)
        dom = BeautifulSoup(res.data)
        assert "Sample Project" in str(res.data), res.data
        assert '5 of 10' in str(res.data), res.data
        err_msg = "Download Partial results button should be shown"
        assert dom.find(id='partialdownload') is not None, err_msg

        for i in range(5):
            task_run = TaskRun(project_id=project.id, task_id=1,
                               info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()
            self.app.get('api/project/%s/newtask' % project.id)

        self.signout()

        project = db.session.query(Project).first()

        res = self.app.get('project/%s/tasks/browse' % (project.short_name),
                           follow_redirects=True)
        assert "Sample Project" in str(res.data), res.data
        msg = 'Task <span class="label label-success">#1</span>'
        assert msg in str(res.data), res.data
        assert '10 of 10' in str(res.data), res.data
        dom = BeautifulSoup(res.data)
        err_msg = "Download Full results button should be shown"
        assert dom.find(id='fulldownload') is not None, err_msg

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_17_export_task_runs(self, mock):
        """Test WEB TaskRun export works"""
        self.register()
        self.new_project()

        project = db.session.query(Project).first()
        task = Task(project_id=project.id, n_answers=10)
        db.session.add(task)
        db.session.commit()

        for i in range(10):
            task_run = TaskRun(project_id=project.id, task_id=1, info={'answer': 1})
            db.session.add(task_run)
            db.session.commit()

        project = db.session.query(Project).first()
        res = self.app.get('project/%s/%s/results.json' % (project.short_name, 1),
                           follow_redirects=True)
        data = json.loads(res.data)
        assert len(data) == 10, data
        for tr in data:
            assert tr['info']['answer'] == 1, tr

        # Check with correct project but wrong task id
        res = self.app.get('project/%s/%s/results.json' % (project.short_name, 5000),
                           follow_redirects=True)
        assert res.status_code == 404, res.status_code

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_18_task_status_wip(self, mock):
        """Test WEB Task Status on going works"""
        self.register()
        self.new_project()

        project = db.session.query(Project).first()
        project.published = True
        task = Task(project_id=project.id, n_answers=10)
        db.session.add(task)
        db.session.commit()
        self.signout()

        project = db.session.query(Project).first()

        res = self.app.get('project/%s/tasks/browse' % (project.short_name),
                           follow_redirects=True)
        assert "Sample Project" in str(res.data), res.data
        msg = 'Task <span class="label label-info">#1</span>'
        assert msg in str(res.data), res.data
        assert '0 of 10' in str(res.data), res.data

        # For a non existing page
        res = self.app.get('project/%s/tasks/browse/5000' % (project.short_name),
                           follow_redirects=True)
        assert res.status_code == 404, res.status_code

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_18_task_status_wip_json(self, mock):
        """Test WEB Task Status on going works"""
        self.register()
        self.new_project()

        project = db.session.query(Project).first()
        project.published = True
        task = Task(project_id=project.id, n_answers=10)
        db.session.add(task)
        db.session.commit()
        self.signout()

        project = db.session.query(Project).first()

        res = self.app_get_json('project/%s/tasks/browse' % (project.short_name))
        data = json.loads(res.data)
        err_msg = 'key missing'
        assert 'n_completed_tasks' in str(data), err_msg
        assert 'n_tasks' in str(data), err_msg
        assert 'n_volunteers' in str(data), err_msg
        assert 'overall_progress' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'pagination' in str(data), err_msg
        assert 'pro_features' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'tasks' in str(data), err_msg
        assert 'template' in str(data), err_msg
        assert 'title' in str(data), err_msg

        assert "Sample Project" in data['title'], data
        assert data['tasks'][0]['n_answers'] == 10, data

        # For a non existing page
        res = self.app_get_json('project/%s/tasks/browse/5000' % (project.short_name))
        assert res.status_code == 404, res.status_code

    @with_context
    def test_19_app_index_categories(self):
        """Test WEB Project Index categories works"""
        self.register()
        self.create()
        self.signout()

        res = self.app.get('project/category/featured', follow_redirects=True)
        assert "Projects" in str(res.data), res.data
        assert Fixtures.cat_1 in str(res.data), res.data

        task = db.session.query(Task).get(1)
        # Update one task to have more answers than expected
        task.n_answers = 1
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).get(1)
        cat = db.session.query(Category).get(1)
        url = '/project/category/%s/' % Fixtures.cat_1
        res = self.app.get(url, follow_redirects=True)
        tmp = '%s Projects' % Fixtures.cat_1
        assert tmp in str(res.data), res

    @with_context
    def test_app_index_categories_pagination(self):
        """Test WEB Project Index categories pagination works"""
        from flask import current_app
        n_apps = current_app.config.get('APPS_PER_PAGE')
        current_app.config['APPS_PER_PAGE'] = 1
        category = CategoryFactory.create(name='category', short_name='cat')
        for project in ProjectFactory.create_batch(2, category=category):
            TaskFactory.create(project=project)
        page1 = self.app.get('/project/category/%s/' % category.short_name)
        page2 = self.app.get('/project/category/%s/page/2/' % category.short_name)
        current_app.config['APPS_PER_PAGE'] = n_apps

        assert '<a href="/project/category/cat/page/2/" rel="nofollow">' in str(page1.data)
        assert page2.status_code == 200, page2.status_code
        assert '<a href="/project/category/cat/" rel="nofollow">' in str(page2.data)

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_20_app_index_published(self, mock):
        """Test WEB Project Index published works"""
        self.register()
        self.new_project()
        self.update_project(new_category_id="1")
        project = db.session.query(Project).first()
        project.published = True
        db.session.commit()
        self.signout()

        res = self.app.get('project/category/featured', follow_redirects=True)
        assert "%s Projects" % Fixtures.cat_1 in str(res.data), res.data
        assert "draft" not in str(res.data), res.data
        assert "Sample Project" in str(res.data), res.data

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_20_json_project_index_draft(self, mock):
        """Test WEB JSON Project Index draft works"""
        # Create root
        self.register()
        self.new_project()
        self.signout()
        # Create a user
        self.register(fullname="jane", name="jane", email="jane@jane.com")
        self.signout()

        # As Anonymous
        res = self.app_get_json('/project/category/draft/', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous should not see draft apps"
        assert dom.find(id='signin') is not None, err_msg

        # As authenticated but not admin
        self.signin(email="jane@jane.com", password="p4ssw0rd")
        res = self.app_get_json('/project/category/draft/', follow_redirects=True)
        data = json.loads(res.data)
        assert res.status_code == 403, "Non-admin should not see draft apps"
        assert data.get('code') == 403, data
        self.signout()

        # As Admin
        self.signin()
        res = self.app_get_json('/project/category/draft/')
        data = json.loads(res.data)
        project = project_repo.get(1)
        assert 'pagination' in list(data.keys()), data
        assert 'active_cat' in list(data.keys()), data
        assert 'categories' in list(data.keys()), data
        assert 'projects' in list(data.keys()), data
        assert data['pagination']['next'] is False, data
        assert data['pagination']['prev'] is False, data
        assert data['pagination']['total'] == 1, data
        assert data['active_cat']['name'] == 'Draft', data
        assert len(data['projects']) == 1, data
        assert data['projects'][0]['id'] == project.id, data


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_20_app_index_draft(self, mock):
        """Test WEB Project Index draft works"""
        # Create root
        self.register()
        self.new_project()
        self.signout()
        # Create a user
        self.register(fullname="jane", name="jane", email="jane@jane.com")
        self.signout()

        # As Anonymous
        res = self.app.get('/project/category/draft', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "Anonymous should not see draft apps"
        assert dom.find(id='signin') is not None, err_msg

        # As authenticated but not admin
        self.signin(email="jane@jane.com", password="p4ssw0rd")
        res = self.app.get('/project/category/draft', follow_redirects=True)
        assert res.status_code == 403, "Non-admin should not see draft apps"
        self.signout()

        # As Admin
        self.signin()
        res = self.app.get('/project/category/draft', follow_redirects=True)
        assert "project-published" not in str(res.data), res.data
        assert "draft" in str(res.data), res.data
        assert "Sample Project" in str(res.data), res.data
        assert 'Draft Projects' in str(res.data), res.data

    @with_context
    def test_21_get_specific_ongoing_task_anonymous(self):
        """Test WEB get specific ongoing task_id for
        a project works as anonymous"""
        self.create()
        self.delete_task_runs()
        project = db.session.query(Project).first()
        task = db.session.query(Task)\
                 .filter(Project.id == project.id)\
                 .first()
        res = self.app.get('project/%s/task/%s' % (project.short_name, task.id),
                           follow_redirects=True)
        assert 'TaskPresenter' in str(res.data), res.data
        msg = "?next=%2Fproject%2F" + project.short_name + "%2Ftask%2F" + str(task.id)
        assert msg in str(res.data), res.data

        # Try with only registered users
        project.allow_anonymous_contributors = False
        db.session.add(project)
        db.session.commit()
        res = self.app.get('project/%s/task/%s' % (project.short_name, task.id),
                           follow_redirects=True)
        assert "sign in to participate" in str(res.data)

    @with_context
    def test_21_get_specific_ongoing_task_anonymous_json(self):
        """Test WEB get specific ongoing task_id for
        a project works as anonymous"""
        self.create()
        self.delete_task_runs()
        project = db.session.query(Project).first()
        task = db.session.query(Task)\
                 .filter(Project.id == project.id)\
                 .first()
        res = self.app_get_json('project/%s/task/%s' % (project.short_name, task.id))
        data = json.loads(res.data)
        err_msg = 'field missing'
        assert 'flash' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'status' in str(data), err_msg
        assert 'template' in str(data), err_msg
        assert 'title' in str(data), err_msg
        err_msg = 'wrong field value'
        assert data['status'] == 'warning', err_msg
        assert data['template'] == '/projects/presenter.html', err_msg
        assert 'Contribute' in data['title'], err_msg
        err_msg = 'private field data exposed'
        assert 'api_key' not in data['owner'], err_msg
        assert 'email_addr' not in data['owner'], err_msg
        assert 'secret_key' not in data['project'], err_msg

        # Try with only registered users
        project.allow_anonymous_contributors = False
        db.session.add(project)
        db.session.commit()
        res = self.app_get_json('project/%s/task/%s' % (project.short_name, task.id))
        assert res.status_code == 302

    @with_context
    def test_23_get_specific_ongoing_task_user(self):
        """Test WEB get specific ongoing task_id for a project works as an user"""
        self.create()
        self.delete_task_runs()
        self.register()
        self.signin()
        project = db.session.query(Project).first()
        task = db.session.query(Task).filter(Project.id == project.id).first()
        res = self.app.get('project/%s/task/%s' % (project.short_name, task.id),
                           follow_redirects=True)
        assert 'TaskPresenter' in str(res.data), res.data

    @with_context
    def test_23_get_specific_ongoing_task_user_json(self):
        """Test WEB get specific ongoing task_id for a project works as an user"""
        self.create()
        self.delete_task_runs()
        self.register()
        self.signin()
        project = db.session.query(Project).first()
        task = db.session.query(Task).filter(Project.id == project.id).first()
        res = self.app_get_json('project/%s/task/%s' % (project.short_name, task.id))
        data = json.loads(res.data)
        err_msg = 'field missing'
        assert 'owner' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'template' in str(data), err_msg
        assert 'title' in str(data), err_msg
        err_msg = 'wrong field value'
        assert data['template'] == '/projects/presenter.html', err_msg
        assert 'Contribute' in data['title'], err_msg
        err_msg = 'private field data exposed'
        assert 'api_key' not in data['owner'], err_msg
        assert 'email_addr' not in data['owner'], err_msg
        assert 'secret_key' not in data['project'], err_msg
        err_msg = 'this field should not existing'
        assert 'flash' not in str(data), err_msg
        assert 'status' not in str(data), err_msg

    @with_context
    @patch('pybossa.view.projects.ContributionsGuard')
    def test_get_specific_ongoing_task_marks_task_as_requested(self, guard):
        fake_guard_instance = mock_contributions_guard()
        guard.return_value = fake_guard_instance
        self.create()
        self.register()
        project = db.session.query(Project).first()
        task = db.session.query(Task).filter(Project.id == project.id).first()
        res = self.app.get('project/%s/task/%s' % (project.short_name, task.id),
                           follow_redirects=True)

        assert fake_guard_instance.stamp.called

    @with_context
    @patch('pybossa.view.projects.ContributionsGuard')
    def test_get_specific_ongoing_task_marks_task_as_requested_json(self, guard):
        fake_guard_instance = mock_contributions_guard()
        guard.return_value = fake_guard_instance
        self.create()
        self.register()
        project = db.session.query(Project).first()
        task = db.session.query(Task).filter(Project.id == project.id).first()
        res = self.app_get_json('project/%s/task/%s' % (project.short_name, task.id))
        print(res.data)

        assert fake_guard_instance.stamp.called


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_25_get_wrong_task_app(self, mock):
        """Test WEB get wrong task.id for a project works"""
        self.create()
        project1 = db.session.query(Project).get(1)
        project1_short_name = project1.short_name

        db.session.query(Task).filter(Task.project_id == 1).first()

        self.register()
        self.new_project()
        app2 = db.session.query(Project).get(2)
        self.new_task(app2.id)
        task2 = db.session.query(Task).filter(Task.project_id == 2).first()
        task2_id = task2.id
        self.signout()

        res = self.app.get('/project/%s/task/%s' % (project1_short_name, task2_id))
        assert "Error" in str(res.data), res.data
        msg = "This task does not belong to %s" % project1_short_name
        assert msg in str(res.data), res.data

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_25_get_wrong_task_app_json(self, mock):
        """Test WEB get wrong task.id for a project works"""
        self.create()
        project1 = db.session.query(Project).get(1)
        project1_short_name = project1.short_name

        db.session.query(Task).filter(Task.project_id == 1).first()

        self.register()
        self.new_project()
        app2 = db.session.query(Project).get(2)
        self.new_task(app2.id)
        task2 = db.session.query(Task).filter(Task.project_id == 2).first()
        task2_id = task2.id
        self.signout()

        res = self.app_get_json('/project/%s/task/%s' % (project1_short_name, task2_id))
        print(res.data)
        data = json.loads(res.data)
        assert 'flash' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'status' in str(data), err_msg
        assert 'template' in str(data), err_msg
        assert 'title' in str(data), err_msg
        err_msg = 'wrong field value'
        assert data['status'] == 'warning', err_msg
        assert data['template'] == '/projects/task/wrong.html', err_msg
        assert 'Contribute' in data['title'], err_msg
        err_msg = 'private field data exposed'
        assert 'api_key' not in data['owner'], err_msg
        assert 'email_addr' not in data['owner'], err_msg
        assert 'secret_key' not in data['project'], err_msg

    @with_context
    def test_26_tutorial_signed_user(self):
        """Test WEB tutorials work as signed in user"""
        self.create()
        project1 = db.session.query(Project).get(1)
        project1.info = dict(tutorial="some help", task_presenter="presenter")
        db.session.commit()
        self.register()
        # First time accessing the project should redirect me to the tutorial
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        err_msg = "There should be some tutorial for the project"
        assert "some help" in str(res.data), err_msg
        # Second time should give me a task, and not the tutorial
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        assert "some help" not in str(res.data)

        # Check if the tutorial can be accessed directly
        res = self.app.get('/project/test-app/tutorial', follow_redirects=True)
        err_msg = "There should be some tutorial for the project"
        assert "some help" in str(res.data), err_msg

    @with_context
    def test_26_tutorial_signed_user_json(self):
        """Test WEB tutorials work as signed in user"""
        self.create()
        project1 = db.session.query(Project).get(1)
        project1.info = dict(tutorial="some help", task_presenter="presenter")
        db.session.commit()
        self.register()
        # First time accessing the project should redirect me to the tutorial
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        err_msg = "There should be some tutorial for the project"
        assert "some help" in str(res.data), err_msg
        # Second time should give me a task, and not the tutorial
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        assert "some help" not in str(res.data)

        # Check if the tutorial can be accessed directly
        res = self.app_get_json('/project/test-app/tutorial')
        data = json.loads(res.data)
        err_msg = 'key missing'
        assert 'owner' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'template' in str(data), err_msg
        assert 'title' in str(data), err_msg
        err_msg = 'project tutorial missing'
        assert 'My New Project' in data['title'], err_msg

    @with_context
    def test_27_tutorial_anonymous_user(self):
        """Test WEB tutorials work as an anonymous user"""
        self.create()
        project = db.session.query(Project).get(1)
        project.info = dict(tutorial="some help", task_presenter="presenter")
        db.session.commit()
        # First time accessing the project should redirect me to the tutorial
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        err_msg = "There should be some tutorial for the project"
        assert "some help" in str(res.data), err_msg
        # Second time should give me a task, and not the tutorial
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        assert "some help"  not in str(res.data)

        # Check if the tutorial can be accessed directly
        res = self.app.get('/project/test-app/tutorial', follow_redirects=True)
        err_msg = "There should be some tutorial for the project"
        assert "some help" in str(res.data), err_msg

    @with_context
    def test_27_tutorial_anonymous_user_json(self):
        """Test WEB tutorials work as an anonymous user"""
        self.create()
        project = db.session.query(Project).get(1)
        project.info = dict(tutorial="some help", task_presenter="presenter")
        db.session.commit()
        # First time accessing the project should redirect me to the tutorial
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        err_msg = "There should be some tutorial for the project"
        assert "some help" in str(res.data), err_msg
        # Second time should give me a task, and not the tutorial
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        assert "some help"  not in str(res.data)

        # Check if the tutorial can be accessed directly
        res = self.app_get_json('/project/test-app/tutorial')
        data = json.loads(res.data)
        err_msg = 'key missing'
        assert 'owner' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'template' in str(data), err_msg
        assert 'title' in str(data), err_msg
        err_msg = 'project tutorial missing'
        assert 'My New Project' in data['title'], err_msg

    @with_context
    def test_28_non_tutorial_signed_user(self):
        """Test WEB project without tutorial work as signed in user"""
        self.create()
        project = db.session.query(Project).get(1)
        project.info = dict(task_presenter="the real presenter")
        db.session.commit()
        self.register()
        # First time accessing the project should show the presenter
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        err_msg = "There should be a presenter for the project"
        assert "the real presenter" in str(res.data), err_msg
        # Second time accessing the project should show the presenter
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        assert "the real presenter" in str(res.data), err_msg

    @with_context
    def test_29_non_tutorial_anonymous_user(self):
        """Test WEB project without tutorials work as an anonymous user"""
        self.create()
        project = db.session.query(Project).get(1)
        project.info = dict(task_presenter="the real presenter")
        db.session.commit()
        # First time accessing the project should show the presenter
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        err_msg = "There should be a presenter for the project"
        assert "the real presenter" in str(res.data), err_msg
        # Second time accessing the project should show the presenter
        res = self.app.get('/project/test-app/newtask', follow_redirects=True)
        assert "the real presenter" in str(res.data), err_msg

    @with_context
    def test_message_is_flashed_contributing_to_project_without_presenter(self):
        project = ProjectFactory.create(info={})
        task = TaskFactory.create(project=project)
        newtask_url = '/project/%s/newtask' % project.short_name
        task_url = '/project/%s/task/%s' % (project.short_name, task.id)
        message = ("Sorry, but this project is still a draft and does "
                   "not have a task presenter.")

        newtask_response = self.app.get(newtask_url, follow_redirects=True)
        task_response = self.app.get(task_url, follow_redirects=True)

        assert message in newtask_response.data
        assert message in task_response.data

    @with_context
    def test_message_is_flashed_contributing_to_project_without_presenter(self):
        """Test task_presenter check is not raised."""
        project = ProjectFactory.create(info={})
        task = TaskFactory.create(project=project)
        newtask_url = '/project/%s/newtask' % project.short_name
        task_url = '/project/%s/task/%s' % (project.short_name, task.id)
        message = ("Sorry, but this project is still a draft and does "
                   "not have a task presenter.")
        with patch.dict(self.flask_app.config,
                        {'DISABLE_TASK_PRESENTER': True}):
            newtask_response = self.app.get(newtask_url)
            task_response = self.app.get(task_url, follow_redirects=True)

            assert message not in str(newtask_response.data), newtask_response.data
            assert message not in str(task_response.data), task_response.data

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_30_app_id_owner(self, mock):
        """Test WEB project settings page shows the ID to the owner"""
        self.register()
        self.new_project()

        res = self.app.get('/project/sampleapp/settings', follow_redirects=True)
        assert "Sample Project" in str(res.data), ("Project should be shown to "
                                              "the owner")
        # TODO: Needs discussion. Disable for now.
        # msg = '<strong><i class="icon-cog"></i> ID</strong>: 1'
        # err_msg = "Project ID should be shown to the owner"
        # assert msg in str(res.data), err_msg

        self.signout()
        self.create()
        self.signin(email=Fixtures.email_addr2, password=Fixtures.password)
        res = self.app.get('/project/sampleapp/settings', follow_redirects=True)
        assert res.status_code == 403, res.status_code

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    @patch('pybossa.ckan.requests.get')
    def test_30_app_id_anonymous_user(self, Mock, mock):
        """Test WEB project page does not show the ID to anonymous users"""
        html_request = FakeResponse(text=json.dumps(self.pkg_json_not_found),
                                    status_code=200,
                                    headers={'content-type': 'application/json'},
                                    encoding='utf-8')
        Mock.return_value = html_request

        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        project.published = True
        db.session.commit()
        self.signout()

        res = self.app.get('/project/sampleapp', follow_redirects=True)
        assert "Sample Project" in str(res.data), ("Project name should be shown"
                                              " to users")
        assert '<strong><i class="icon-cog"></i> ID</strong>: 1' not in \
            str(res.data), "Project ID should be shown to the owner"

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_31_user_profile_progress(self, mock):
        """Test WEB user progress profile page works"""
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        task = Task(project_id=project.id, n_answers=10)
        db.session.add(task)
        task_run = TaskRun(project_id=project.id, task_id=1, user_id=1,
                           info={'answer': 1})
        db.session.add(task_run)
        db.session.commit()

        res = self.app.get('account/johndoe', follow_redirects=True)
        assert "Sample Project" in str(res.data)

    @with_context
    def test_32_oauth_password(self):
        """Test WEB user sign in without password works"""
        user = User(email_addr="johndoe@johndoe.com",
                    name="John Doe",
                    passwd_hash=None,
                    fullname="johndoe",
                    api_key="api-key")
        db.session.add(user)
        db.session.commit()
        res = self.signin()
        assert "Ooops, we didn&#39;t find you in the system" in str(res.data), res.data

    @with_context
    def test_39_google_oauth_creation(self):
        """Test WEB Google OAuth creation of user works"""
        fake_response = {
            'access_token': 'access_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'id_token': 'token'}

        fake_user = {
            'family_name': 'Doe', 'name': 'John Doe',
            'picture': 'https://goo.gl/img.jpg',
            'locale': 'en',
            'gender': 'male',
            'email': 'john@gmail.com',
            'birthday': '0000-01-15',
            'link': 'https://plus.google.com/id',
            'given_name': 'John',
            'id': '111111111111111111111',
            'verified_email': True}

        from pybossa.view import google
        response_user = google.manage_user(fake_response['access_token'],
                                           fake_user)

        user = db.session.query(User).get(1)

        assert user.email_addr == response_user.email_addr, response_user

    @with_context
    def test_40_google_oauth_creation(self):
        """Test WEB Google OAuth detects same user name/email works"""
        fake_response = {
            'access_token': 'access_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'id_token': 'token'}

        fake_user = {
            'family_name': 'Doe', 'name': 'John Doe',
            'picture': 'https://goo.gl/img.jpg',
            'locale': 'en',
            'gender': 'male',
            'email': 'john@gmail.com',
            'birthday': '0000-01-15',
            'link': 'https://plus.google.com/id',
            'given_name': 'John',
            'id': '111111111111111111111',
            'verified_email': True}

        self.register()
        self.signout()

        from pybossa.view import google
        response_user = google.manage_user(fake_response['access_token'],
                                           fake_user)

        assert response_user is None, response_user

    @with_context
    def test_39_facebook_oauth_creation(self):
        """Test WEB Facebook OAuth creation of user works"""
        fake_response = {
            'access_token': 'access_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'id_token': 'token'}

        fake_user = {
            'username': 'teleyinex',
            'first_name': 'John',
            'last_name': 'Doe',
            'verified': True,
            'name': 'John Doe',
            'locale': 'en_US',
            'gender': 'male',
            'email': 'johndoe@example.com',
            'quotes': '"quote',
            'link': 'http://www.facebook.com/johndoe',
            'timezone': 1,
            'updated_time': '2011-11-11T12:33:52+0000',
            'id': '11111'}

        from pybossa.view import facebook
        response_user = facebook.manage_user(fake_response['access_token'],
                                             fake_user)

        user = db.session.query(User).get(1)

        assert user.email_addr == response_user.email_addr, response_user

    @with_context
    def test_40_facebook_oauth_creation(self):
        """Test WEB Facebook OAuth detects same user name/email works"""
        fake_response = {
            'access_token': 'access_token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'id_token': 'token'}

        fake_user = {
            'username': 'teleyinex',
            'first_name': 'John',
            'last_name': 'Doe',
            'verified': True,
            'name': 'John Doe',
            'locale': 'en_US',
            'gender': 'male',
            'email': 'johndoe@example.com',
            'quotes': '"quote',
            'link': 'http://www.facebook.com/johndoe',
            'timezone': 1,
            'updated_time': '2011-11-11T12:33:52+0000',
            'id': '11111'}

        self.register()
        self.signout()

        from pybossa.view import facebook
        response_user = facebook.manage_user(fake_response['access_token'],
                                             fake_user)

        assert response_user is None, response_user

    @with_context
    def test_39_twitter_oauth_creation(self):
        """Test WEB Twitter OAuth creation of user works"""
        fake_response = {
            'access_token': {'oauth_token': 'oauth_token',
                              'oauth_token_secret': 'oauth_token_secret'},
            'token_type': 'Bearer',
            'expires_in': 3600,
            'id_token': 'token'}

        fake_user = {'screen_name': 'johndoe',
                     'user_id': '11111'}

        from pybossa.view import twitter
        response_user = twitter.manage_user(fake_response['access_token'],
                                            fake_user)

        user = db.session.query(User).get(1)

        assert user.email_addr == response_user.email_addr, response_user

        res = self.signin(email=user.email_addr, password='wrong')
        msg = "It seems like you signed up with your Twitter account"
        assert msg in str(res.data), msg

    @with_context
    def test_40_twitter_oauth_creation(self):
        """Test WEB Twitter OAuth detects same user name/email works"""
        fake_response = {
            'access_token': {'oauth_token': 'oauth_token',
                              'oauth_token_secret': 'oauth_token_secret'},
            'token_type': 'Bearer',
            'expires_in': 3600,
            'id_token': 'token'}

        fake_user = {'screen_name': 'johndoe',
                     'user_id': '11111'}

        self.register()
        self.signout()

        from pybossa.view import twitter
        response_user = twitter.manage_user(fake_response['access_token'],
                                            fake_user)

        assert response_user is None, response_user

    @with_context
    def test_41_password_change_json(self):
        """Test WEB password JSON changing"""
        password = "mehpassword"
        self.register(password=password)
        url = '/account/johndoe/update'
        csrf = self.get_csrf(url)
        payload = {'current_password': password,
                   'new_password': "p4ssw0rd",
                   'confirm': "p4ssw0rd",
                   'btn': 'Password'}
        res = self.app.post(url,
                            data=json.dumps(payload),
                            follow_redirects=False,
                            content_type="application/json",
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert "Yay, you changed your password succesfully!" == data.get('flash'), res.data
        assert data.get('status') == SUCCESS, data

        password = "p4ssw0rd"
        self.signin(password=password)
        payload['current_password'] = "wrongpasswor"
        res = self.app.post(url,
                            data=json.dumps(payload),
                            follow_redirects=False,
                            content_type="application/json",
                            headers={'X-CSRFToken': csrf})
        msg = "Your current password doesn't match the one in our records"
        data = json.loads(res.data)
        assert msg == data.get('flash'), data
        assert data.get('status') == ERROR, data

        res = self.app.post('/account/johndoe/update',
                            data=json.dumps({'current_password': '',
                                  'new_password': '',
                                  'confirm': '',
                                  'btn': 'Password'}),
                            follow_redirects=False,
                            content_type="application/json",
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        msg = "Please correct the errors"
        err_msg = "There should be a flash message"
        assert data.get('flash') == msg, (err_msg, data)
        assert data.get('status') == ERROR, (err_msg, data)

    @with_context
    def test_42_avatar_change_json(self):
        """Test WEB avatar JSON changing"""
        import io
        self.register()
        user = user_repo.get_by(name='johndoe')
        print(user)
        url = '/account/johndoe/update'
        csrf = self.get_csrf(url)
        payload = {'avatar': (io.BytesIO(b"abcdef"), 'test.jpg'),
                   'id': user.id,
                   'x1': "100",
                   'x2': '100',
                   'y1': '300',
                   'y2': '300',
                   'btn': 'Upload'}
        res = self.app.post(url,
                            data=payload,
                            follow_redirects=True,
                            content_type="multipart/form-data",
                            headers={'X-CSRFToken': csrf})
        err_msg = "Avatar should be updated"
        assert "Your avatar has been updated!" in str(res.data), (res.data, err_msg)

        payload['avatar'] = None
        res = self.app.post(url,
                            data=payload,
                            follow_redirects=True,
                            content_type="multipart/form-data",
                            headers={'X-CSRFToken': csrf})
        msg = "You have to provide an image file to update your avatar"
        assert msg in str(res.data), (res.data, msg)

    @with_context
    def test_41_password_change(self):
        """Test WEB password changing"""
        password = "mehpassword"
        self.register(password=password)
        res = self.app.post('/account/johndoe/update',
                            data={'current_password': password,
                                  'new_password': "p4ssw0rd",
                                  'confirm': "p4ssw0rd",
                                  'btn': 'Password'},
                            follow_redirects=True)
        assert "Yay, you changed your password succesfully!" in str(res.data), res.data

        password = "p4ssw0rd"
        self.signin(password=password)
        res = self.app.post('/account/johndoe/update',
                            data={'current_password': "wrongpassword",
                                  'new_password': "p4ssw0rd",
                                  'confirm': "p4ssw0rd",
                                  'btn': 'Password'},
                            follow_redirects=True)
        msg = "Your current password doesn&#39;t match the one in our records"
        assert msg in str(res.data)

        res = self.app.post('/account/johndoe/update',
                            data={'current_password': '',
                                  'new_password': '',
                                  'confirm': '',
                                  'btn': 'Password'},
                            follow_redirects=True)
        msg = "Please correct the errors"
        assert msg in str(res.data)

    @with_context
    @patch('pybossa.view.account.super_queue.enqueue')
    def test_delete_account(self, mock):
        """Test WEB delete account works"""
        from pybossa.jobs import delete_account
        self.register()
        res = self.app.get('/account/johndoe/delete')
        assert res.status_code == 302, res.status_code
        assert 'account/signout' in str(res.data)
        user = user_repo.filter_by(name='johndoe')[0]
        mock.assert_called_with(delete_account, user.id)

    @with_context
    @patch('pybossa.view.account.super_queue.enqueue')
    def test_delete_account_anon(self, mock):
        """Test WEB delete account anon fails"""
        from pybossa.jobs import delete_account
        self.register()
        self.signout()
        res = self.app.get('/account/johndoe/delete')
        assert res.status_code == 302, res.status_code
        assert 'account/signin?next' in str(res.data)

    @with_context
    @patch('pybossa.view.account.super_queue.enqueue')
    def test_delete_account_json_anon(self, mock):
        """Test WEB delete account json anon fails"""
        from pybossa.jobs import delete_account
        self.register()
        self.signout()
        res = self.app_get_json('/account/johndoe/delete')
        assert res.status_code == 302, res.status_code
        assert 'account/signin?next' in str(res.data)

    @with_context
    @patch('pybossa.view.account.super_queue.enqueue')
    def test_delete_account_other_user(self, mock):
        """Test WEB delete account other user fails"""
        from pybossa.jobs import delete_account
        user = UserFactory.create(id=5000)
        self.register()
        res = self.app.get('/account/%s/delete' % user.name)
        assert res.status_code == 403, res.status_code

    @with_context
    @patch('pybossa.view.account.super_queue.enqueue')
    def test_delete_account_json_other_user(self, mock):
        """Test WEB delete account json anon fails"""
        from pybossa.jobs import delete_account
        user = UserFactory.create(id=5001)
        self.register()
        res = self.app_get_json('/account/%s/delete' % user.name)
        assert res.status_code == 403, (res.status_code, res.data)

    @with_context
    @patch('pybossa.view.account.super_queue.enqueue')
    def test_delete_account_404_user(self, mock):
        """Test WEB delete account user does not exists"""
        from pybossa.jobs import delete_account
        self.register()
        res = self.app.get('/account/juan/delete')
        assert res.status_code == 404, res.status_code

    @with_context
    @patch('pybossa.view.account.super_queue.enqueue')
    def test_delete_account_json_404_user(self, mock):
        """Test WEB delete account json user does not exist"""
        from pybossa.jobs import delete_account
        self.register()
        res = self.app_get_json('/account/asdafsdlw/delete')
        assert res.status_code == 404, (res.status_code, res.data)

    @with_context
    @patch('pybossa.view.account.super_queue.enqueue')
    def test_delete_account_json(self, mock):
        """Test WEB JSON delete account works"""
        from pybossa.jobs import delete_account
        self.register()
        res = self.app_get_json('/account/johndoe/delete')
        data = json.loads(res.data)
        assert data['job'] == 'enqueued', data
        user = user_repo.filter_by(name='johndoe')[0]
        mock.assert_called_with(delete_account, user.id)

    @with_context
    def test_42_password_link(self):
        """Test WEB visibility of password change link"""
        self.register()
        res = self.app.get('/account/johndoe/update')
        assert "Change your Password" in str(res.data)
        user = User.query.get(1)
        user.twitter_user_id = 1234
        db.session.add(user)
        db.session.commit()
        res = self.app.get('/account/johndoe/update')
        assert "Change your Password" not in str(res.data), res.data

    @with_context
    def test_43_terms_of_use_and_data(self):
        """Test WEB terms of use is working"""
        res = self.app.get('account/signin', follow_redirects=True)
        assert "/help/terms-of-use" in str(res.data), res.data
        assert "http://opendatacommons.org/licenses/by/" in str(res.data), res.data

        res = self.app.get('account/register', follow_redirects=True)
        assert "http://okfn.org/terms-of-use/" in str(res.data), res.data
        assert "http://opendatacommons.org/licenses/by/" in str(res.data), res.data

    @with_context
    def test_help_endpoint(self):
        """Test WEB help endpoint is working"""
        res = self.app.get('help/', follow_redirects=True)


    @with_context
    @patch('pybossa.view.account.signer.loads')
    def test_44_password_reset_json_key_errors(self, Mock):
        """Test WEB password reset JSON key errors are caught"""
        self.register()
        user = User.query.get(1)
        userdict = {'user': user.name, 'password': user.passwd_hash}
        fakeuserdict = {'user': user.name, 'password': 'wronghash'}
        fakeuserdict_err = {'user': user.name, 'passwd': 'some'}
        fakeuserdict_form = {'user': user.name, 'passwd': 'p4ssw0rD'}
        key = signer.dumps(userdict, salt='password-reset')
        returns = [BadSignature('Fake Error'), BadSignature('Fake Error'), userdict,
                   fakeuserdict, userdict, userdict, fakeuserdict_err]

        def side_effects(*args, **kwargs):
            result = returns.pop(0)
            if isinstance(result, BadSignature):
                raise result
            return result
        Mock.side_effect = side_effects
        # Request with no key
        content_type = 'application/json'
        res = self.app_get_json('/account/reset-password')
        assert 403 == res.status_code
        data = json.loads(res.data)
        assert data.get('code') == 403, data
        # Request with invalid key
        res = self.app_get_json('/account/reset-password?key=foo')
        assert 403 == res.status_code
        data = json.loads(res.data)
        assert data.get('code') == 403, data

        # Request with key exception
        res = self.app_get_json('/account/reset-password?key=%s' % (key))
        assert 403 == res.status_code
        data = json.loads(res.data)
        assert data.get('code') == 403, data

        res = self.app_get_json('/account/reset-password?key=%s' % (key))
        assert 200 == res.status_code
        data = json.loads(res.data)
        assert data.get('form'), data
        assert data.get('form').get('csrf'), data
        keys = ['current_password', 'new_password', 'confirm']
        for key in keys:
            assert key in list(data.get('form').keys()), data

        res = self.app_get_json('/account/reset-password?key=%s' % (key))
        assert 403 == res.status_code
        data = json.loads(res.data)
        assert data.get('code') == 403, data

        # Check validation
        payload = {'new_password': '', 'confirm': '#4a4'}
        res = self.app_post_json('/account/reset-password?key=%s' % (key),
                                 data=payload)


        msg = "Please correct the errors"
        data = json.loads(res.data)
        assert msg in data.get('flash'), data
        assert data.get('form').get('errors'), data
        assert data.get('form').get('errors').get('new_password'), data


        res = self.app_post_json('/account/reset-password?key=%s' % (key),
                                 data={'new_password': 'p4ssw0rD',
                                       'confirm': 'p4ssw0rD'})
        data = json.loads(res.data)
        msg = "You reset your password successfully!"
        assert msg in data.get('flash'), data
        assert data.get('status') == SUCCESS, data


        # Request without password
        res = self.app_get_json('/account/reset-password?key=%s' % (key))
        assert 403 == res.status_code
        data = json.loads(res.data)
        assert data.get('code') == 403, data


    @with_context
    @patch('pybossa.view.account.signer.loads')
    def test_44_password_reset_key_errors(self, Mock):
        """Test WEB password reset key errors are caught"""
        self.register()
        user = User.query.get(1)
        userdict = {'user': user.name, 'password': user.passwd_hash}
        fakeuserdict = {'user': user.name, 'password': 'wronghash'}
        fakeuserdict_err = {'user': user.name, 'passwd': 'some'}
        fakeuserdict_form = {'user': user.name, 'passwd': 'p4ssw0rD'}
        key = signer.dumps(userdict, salt='password-reset')
        returns = [BadSignature('Fake Error'), BadSignature('Fake Error'), userdict,
                   fakeuserdict, userdict, userdict, fakeuserdict_err]

        def side_effects(*args, **kwargs):
            result = returns.pop(0)
            if isinstance(result, BadSignature):
                raise result
            return result
        Mock.side_effect = side_effects
        # Request with no key
        res = self.app.get('/account/reset-password', follow_redirects=True)
        assert 403 == res.status_code
        # Request with invalid key
        res = self.app.get('/account/reset-password?key=foo', follow_redirects=True)
        assert 403 == res.status_code
        # Request with key exception
        res = self.app.get('/account/reset-password?key=%s' % (key), follow_redirects=True)
        assert 403 == res.status_code
        res = self.app.get('/account/reset-password?key=%s' % (key), follow_redirects=True)
        assert 200 == res.status_code
        res = self.app.get('/account/reset-password?key=%s' % (key), follow_redirects=True)
        assert 403 == res.status_code

        # Check validation
        res = self.app.post('/account/reset-password?key=%s' % (key),
                            data={'new_password': '',
                                  'confirm': '#4a4'},
                            follow_redirects=True)

        assert "Please correct the errors" in str(res.data), res.data

        res = self.app.post('/account/reset-password?key=%s' % (key),
                            data={'new_password': 'p4ssw0rD',
                                  'confirm': 'p4ssw0rD'},
                            follow_redirects=True)

        assert "You reset your password successfully!" in str(res.data)

        # Request without password
        res = self.app.get('/account/reset-password?key=%s' % (key), follow_redirects=True)
        assert 403 == res.status_code

    @with_context
    @patch('pybossa.view.account.url_for')
    @patch('pybossa.view.account.mail_queue', autospec=True)
    @patch('pybossa.view.account.signer')
    def test_45_password_reset_link_json(self, signer, queue, mock_url):
        """Test WEB password reset email form"""
        csrf = self.get_csrf('/account/forgot-password')
        res = self.app.post('/account/forgot-password',
                            data=json.dumps({'email_addr': "johndoe@example.com"}),
                            follow_redirects=False,
                            content_type="application/json",
                            headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        err_msg = "Mimetype should be application/json"
        assert res.mimetype == 'application/json', err_msg
        err_msg = "Flash message should be included"
        assert data.get('flash'), err_msg
        assert ("We don't have this email in our records. You may have"
                " signed up with a different email or used Twitter, "
                "Facebook, or Google to sign-in") in data.get('flash'), err_msg

        self.register()
        self.register(name='janedoe')
        self.register(name='google')
        self.register(name='facebook')
        user = User.query.get(1)
        jane = User.query.get(2)
        jane.twitter_user_id = 10
        google = User.query.get(3)
        google.google_user_id = 103
        facebook = User.query.get(4)
        facebook.facebook_user_id = 104
        db.session.add_all([jane, google, facebook])
        db.session.commit()

        data = {'password': user.passwd_hash, 'user': user.name}
        csrf = self.get_csrf('/account/forgot-password')
        res = self.app.post('/account/forgot-password',
                            data=json.dumps({'email_addr': user.email_addr}),
                            follow_redirects=False,
                            content_type="application/json",
                            headers={'X-CSRFToken': csrf})
        resdata = json.loads(res.data)
        signer.dumps.assert_called_with(data, salt='password-reset')
        key = signer.dumps(data, salt='password-reset')
        enqueue_call = queue.enqueue.call_args_list[0]
        assert send_mail == enqueue_call[0][0], "send_mail not called"
        assert 'Click here to recover your account' in enqueue_call[0][1]['body']
        assert 'To recover your password' in enqueue_call[0][1]['html']
        assert mock_url.called_with('.reset_password', key=key, _external=True)
        err_msg = "There should be a flash message"
        assert resdata.get('flash'), err_msg
        assert "sent you an email" in resdata.get('flash'), err_msg

        data = {'password': jane.passwd_hash, 'user': jane.name}
        csrf = self.get_csrf('/account/forgot-password')
        res = self.app.post('/account/forgot-password',
                            data=json.dumps({'email_addr': 'janedoe@example.com'}),
                            follow_redirects=False,
                            content_type="application/json",
                            headers={'X-CSRFToken': csrf})

        resdata = json.loads(res.data)

        enqueue_call = queue.enqueue.call_args_list[1]
        assert send_mail == enqueue_call[0][0], "send_mail not called"
        assert 'your Twitter account to ' in enqueue_call[0][1]['body']
        assert 'your Twitter account to ' in enqueue_call[0][1]['html']
        err_msg = "There should be a flash message"
        assert resdata.get('flash'), err_msg
        assert "sent you an email" in resdata.get('flash'), err_msg

        data = {'password': google.passwd_hash, 'user': google.name}
        csrf = self.get_csrf('/account/forgot-password')
        res = self.app.post('/account/forgot-password',
                            data=json.dumps({'email_addr': 'google@example.com'}),
                            follow_redirects=False,
                            content_type="application/json",
                            headers={'X-CSRFToken': csrf})

        resdata = json.loads(res.data)

        enqueue_call = queue.enqueue.call_args_list[2]
        assert send_mail == enqueue_call[0][0], "send_mail not called"
        assert 'your Google account to ' in enqueue_call[0][1]['body']
        assert 'your Google account to ' in enqueue_call[0][1]['html']
        err_msg = "There should be a flash message"
        assert resdata.get('flash'), err_msg
        assert "sent you an email" in resdata.get('flash'), err_msg

        data = {'password': facebook.passwd_hash, 'user': facebook.name}
        csrf = self.get_csrf('/account/forgot-password')
        res = self.app.post('/account/forgot-password',
                            data=json.dumps({'email_addr': 'facebook@example.com'}),
                            follow_redirects=False,
                            content_type="application/json",
                            headers={'X-CSRFToken': csrf})

        enqueue_call = queue.enqueue.call_args_list[3]
        assert send_mail == enqueue_call[0][0], "send_mail not called"
        assert 'your Facebook account to ' in enqueue_call[0][1]['body']
        assert 'your Facebook account to ' in enqueue_call[0][1]['html']
        err_msg = "There should be a flash message"
        assert resdata.get('flash'), err_msg
        assert "sent you an email" in resdata.get('flash'), err_msg

        # Test with not valid form
        csrf = self.get_csrf('/account/forgot-password')
        res = self.app.post('/account/forgot-password',
                            data=json.dumps({'email_addr': ''}),
                            follow_redirects=False,
                            content_type="application/json",
                            headers={'X-CSRFToken': csrf})

        resdata = json.loads(res.data)
        msg = "Something went wrong, please correct the errors"
        assert msg in resdata.get('flash'), res.data
        assert resdata.get('form').get('errors').get('email_addr') is not None, resdata

        with patch.dict(self.flask_app.config, {'SPA_SERVER_NAME':
                                                'http://local.com'}):
            data = {'password': user.passwd_hash, 'user': user.name}
            csrf = self.get_csrf('/account/forgot-password')
            res = self.app.post('/account/forgot-password',
                                data=json.dumps({'email_addr': user.email_addr}),
                                follow_redirects=False,
                                content_type="application/json",
                                headers={'X-CSRFToken': csrf})
            resdata = json.loads(res.data)
            signer.dumps.assert_called_with(data, salt='password-reset')
            key = signer.dumps(data, salt='password-reset')
            enqueue_call = queue.enqueue.call_args_list[0]
            assert send_mail == enqueue_call[0][0], "send_mail not called"
            assert 'Click here to recover your account' in enqueue_call[0][1]['body']
            assert 'To recover your password' in enqueue_call[0][1]['html']
            assert mock_url.called_with('.reset_password', key=key)
            err_msg = "There should be a flash message"
            assert resdata.get('flash'), err_msg
            assert "sent you an email" in resdata.get('flash'), err_msg


    @with_context
    @patch('pybossa.view.account.mail_queue', autospec=True)
    @patch('pybossa.view.account.signer')
    def test_45_password_reset_link(self, signer, queue):
        """Test WEB password reset email form"""
        res = self.app.post('/account/forgot-password',
                            data={'email_addr': "johndoe@example.com"},
                            follow_redirects=True)
        assert ("We don&#39;t have this email in our records. You may have"
                " signed up with a different email or used Twitter, "
                "Facebook, or Google to sign-in") in str(res.data)

        self.register()
        self.register(name='janedoe')
        self.register(name='google')
        self.register(name='facebook')
        user = User.query.get(1)
        jane = User.query.get(2)
        jane.twitter_user_id = 10
        google = User.query.get(3)
        google.google_user_id = 103
        facebook = User.query.get(4)
        facebook.facebook_user_id = 104
        db.session.add_all([jane, google, facebook])
        db.session.commit()

        data = {'password': user.passwd_hash, 'user': user.name}
        self.app.post('/account/forgot-password',
                      data={'email_addr': user.email_addr},
                      follow_redirects=True)
        signer.dumps.assert_called_with(data, salt='password-reset')
        enqueue_call = queue.enqueue.call_args_list[0]
        assert send_mail == enqueue_call[0][0], "send_mail not called"
        assert 'Click here to recover your account' in enqueue_call[0][1]['body']
        assert 'To recover your password' in enqueue_call[0][1]['html']

        data = {'password': jane.passwd_hash, 'user': jane.name}
        self.app.post('/account/forgot-password',
                      data={'email_addr': 'janedoe@example.com'},
                      follow_redirects=True)
        enqueue_call = queue.enqueue.call_args_list[1]
        assert send_mail == enqueue_call[0][0], "send_mail not called"
        assert 'your Twitter account to ' in enqueue_call[0][1]['body']
        assert 'your Twitter account to ' in enqueue_call[0][1]['html']

        data = {'password': google.passwd_hash, 'user': google.name}
        self.app.post('/account/forgot-password',
                      data={'email_addr': 'google@example.com'},
                      follow_redirects=True)
        enqueue_call = queue.enqueue.call_args_list[2]
        assert send_mail == enqueue_call[0][0], "send_mail not called"
        assert 'your Google account to ' in enqueue_call[0][1]['body']
        assert 'your Google account to ' in enqueue_call[0][1]['html']

        data = {'password': facebook.passwd_hash, 'user': facebook.name}
        self.app.post('/account/forgot-password',
                      data={'email_addr': 'facebook@example.com'},
                      follow_redirects=True)
        enqueue_call = queue.enqueue.call_args_list[3]
        assert send_mail == enqueue_call[0][0], "send_mail not called"
        assert 'your Facebook account to ' in enqueue_call[0][1]['body']
        assert 'your Facebook account to ' in enqueue_call[0][1]['html']

        # Test with not valid form
        res = self.app.post('/account/forgot-password',
                            data={'email_addr': ''},
                            follow_redirects=True)
        msg = "Something went wrong, please correct the errors"
        assert msg in str(res.data), res.data

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_46_tasks_exists(self, mock):
        """Test WEB tasks page works."""
        self.register()
        self.new_project()
        res = self.app.get('/project/sampleapp/tasks/', follow_redirects=True)
        assert "Edit the task presenter" in str(res.data), \
            "Task Presenter Editor should be an option"
        assert_raises(ValueError, json.loads, res.data)

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_46_tasks_exists_json(self, mock):
        """Test WEB tasks json works."""
        self.register()
        self.new_project()
        res = self.app_get_json('/project/sampleapp/tasks/')
        data = json.loads(res.data)
        err_msg = 'Field missing in data'
        assert 'autoimporter_enabled' in str(data), err_msg
        assert 'last_activity' in str(data), err_msg
        assert 'n_completed_tasks' in str(data), err_msg
        assert 'n_task_runs' in str(data), err_msg
        assert 'n_tasks' in str(data), err_msg
        assert 'n_volunteers' in str(data), err_msg
        assert 'overall_progress' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'pro_features' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'template' in str(data), err_msg
        assert 'title' in str(data), err_msg
        assert 'api_key' in data['owner'], err_msg
        assert 'secret_key' in data['project'], err_msg

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_46_tasks_exists_json_other_user(self, mock):
        """Test WEB tasks json works."""
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        project.published = True
        db.session.commit()
        TaskFactory.create(project=project)
        self.signout()
        res = self.app_get_json('/project/sampleapp/tasks/')
        data = json.loads(res.data)
        print(res.data)
        err_msg = 'Field missing in data'
        assert 'autoimporter_enabled' in str(data), err_msg
        assert 'last_activity' in str(data), err_msg
        assert 'n_completed_tasks' in str(data), err_msg
        assert 'n_task_runs' in str(data), err_msg
        assert 'n_tasks' in str(data), err_msg
        assert 'n_volunteers' in str(data), err_msg
        assert 'overall_progress' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        assert 'pro_features' in str(data), err_msg
        assert 'project' in str(data), err_msg
        assert 'template' in str(data), err_msg
        assert 'title' in str(data), err_msg
        err_msg = 'private data should not be exposed'
        assert 'api_key' not in data['owner'], err_msg
        assert 'secret_key' not in data['project'], err_msg


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_47_task_presenter_editor_loads(self, mock):
        """Test WEB task presenter editor loads"""
        self.register()
        self.new_project()
        res = self.app.get('/project/sampleapp/tasks/taskpresentereditor',
                           follow_redirects=True)
        err_msg = "Task Presenter options not found"
        assert "Task Presenter Editor" in str(res.data), err_msg
        err_msg = "Basic template not found"
        assert "The most basic template" in str(res.data), err_msg
        err_msg = "Image Pattern Recognition not found"
        assert "Image Pattern Recognition" in str(res.data), err_msg
        err_msg = "Sound Pattern Recognition not found"
        assert "Sound Pattern Recognition" in str(res.data), err_msg
        err_msg = "Video Pattern Recognition not found"
        assert "Video Pattern Recognition" in str(res.data), err_msg
        err_msg = "Transcribing documents not found"
        assert "Transcribing documents" in str(res.data), err_msg

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_47_task_presenter_editor_loads_json(self, mock):
        """Test WEB task presenter editor JSON loads"""
        self.register()
        self.new_project()
        res = self.app_get_json('/project/sampleapp/tasks/taskpresentereditor')
        data = json.loads(res.data)
        err_msg = "Task Presenter options not found"
        assert "Task Presenter Editor" in data['title'], err_msg
        presenters = ["projects/presenters/basic.html",
                      "projects/presenters/image.html",
                      "projects/presenters/sound.html",
                      "projects/presenters/video.html",
                      "projects/presenters/map.html",
                      "projects/presenters/pdf.html"]
        assert data['presenters'] == presenters, err_msg

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_48_task_presenter_editor_works(self, mock):
        """Test WEB task presenter editor works"""
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        err_msg = "Task Presenter should be empty"
        assert not project.info.get('task_presenter'), err_msg

        res = self.app.get('/project/sampleapp/tasks/taskpresentereditor?template=basic',
                           follow_redirects=True)
        assert "var editor" in str(res.data), "CodeMirror Editor not found"
        assert "Task Presenter" in str(res.data), "CodeMirror Editor not found"
        assert "Task Presenter Preview" in str(res.data), "CodeMirror View not found"
        res = self.app.post('/project/sampleapp/tasks/taskpresentereditor',
                            data={'editor': 'Some HTML code!'},
                            follow_redirects=True)
        assert "Sample Project" in str(res.data), "Does not return to project details"
        project = db.session.query(Project).first()
        err_msg = "Task Presenter failed to update"
        assert project.info['task_presenter'] == 'Some HTML code!', err_msg

        # Check it loads the previous posted code:
        res = self.app.get('/project/sampleapp/tasks/taskpresentereditor',
                           follow_redirects=True)
        assert "Some HTML code" in str(res.data), res.data

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_48_task_presenter_editor_works_json(self, mock):
        """Test WEB task presenter editor works JSON"""
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        err_msg = "Task Presenter should be empty"
        assert not project.info.get('task_presenter'), err_msg

        url = '/project/sampleapp/tasks/taskpresentereditor?template=basic'
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = "there should not be presenters"
        assert data.get('presenters') is None, err_msg
        assert data['form']['csrf'] is not None, data
        assert data['form']['editor'] is not None, data
        res = self.app_post_json(url, data={'editor': 'Some HTML code!'})
        data = json.loads(res.data)
        assert data['status'] == SUCCESS, data
        project = db.session.query(Project).first()
        assert project.info['task_presenter'] == 'Some HTML code!', err_msg

        # Check it loads the previous posted code:
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert data['form']['editor'] == 'Some HTML code!', data

    @with_context
    @patch('pybossa.ckan.requests.get')
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    @patch('pybossa.forms.validator.requests.get')
    def test_48_update_app_info(self, Mock, mock, mock_webhook):
        """Test WEB project update/edit works keeping previous info values"""
        html_request = FakeResponse(text=json.dumps(self.pkg_json_not_found),
                                    status_code=200,
                                    headers={'content-type': 'application/json'},
                                    encoding='utf-8')
        Mock.return_value = html_request

        mock_webhook.return_value = html_request
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        err_msg = "Task Presenter should be empty"
        assert not project.info.get('task_presenter'), err_msg

        res = self.app.post('/project/sampleapp/tasks/taskpresentereditor',
                            data={'editor': 'Some HTML code!'},
                            follow_redirects=True)
        assert "Sample Project" in str(res.data), "Does not return to project details"
        project = db.session.query(Project).first()
        for i in range(10):
            key = "key_%s" % i
            project.info[key] = i
        db.session.add(project)
        db.session.commit()
        _info = project.info

        self.update_project()
        project = db.session.query(Project).first()
        for key in _info:
            assert key in list(project.info.keys()), \
                "The key %s is lost and it should be here" % key
        assert project.name == "Sample Project", "The project has not been updated"
        error_msg = "The project description has not been updated"
        assert project.description == "Description", error_msg
        error_msg = "The project long description has not been updated"
        assert project.long_description == "Long desc", error_msg

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_49_announcement_messages(self, mock):
        """Test WEB announcement messages works"""
        self.register()
        res = self.app.get("/", follow_redirects=True)
        error_msg = "There should be a message for the root user"
        print(res.data)
        assert "Root Message" in str(res.data), error_msg
        error_msg = "There should be a message for the user"
        assert "User Message" in str(res.data), error_msg
        error_msg = "There should not be an owner message"
        assert "Owner Message" not in str(res.data), error_msg
        # Now make the user a project owner
        self.new_project()
        res = self.app.get("/", follow_redirects=True)
        error_msg = "There should be a message for the root user"
        assert "Root Message" in str(res.data), error_msg
        error_msg = "There should be a message for the user"
        assert "User Message" in str(res.data), error_msg
        error_msg = "There should be an owner message"
        assert "Owner Message" in str(res.data), error_msg
        self.signout()

        # Register another user
        self.register(fullname="Jane Doe", name="janedoe",
                      password="janedoe", email="jane@jane.com")
        res = self.app.get("/", follow_redirects=True)
        error_msg = "There should not be a message for the root user"
        assert "Root Message" not in str(res.data), error_msg
        error_msg = "There should be a message for the user"
        assert "User Message" in str(res.data), error_msg
        error_msg = "There should not be an owner message"
        assert "Owner Message" not in str(res.data), error_msg
        self.signout()

        # Now as an anonymous user
        res = self.app.get("/", follow_redirects=True)
        error_msg = "There should not be a message for the root user"
        assert "Root Message" not in str(res.data), error_msg
        error_msg = "There should not be a message for the user"
        assert "User Message" not in str(res.data), error_msg
        error_msg = "There should not be an owner message"
        assert "Owner Message" not in str(res.data), error_msg

    @with_context
    def test_export_user_json(self):
        """Test export user data in JSON."""
        user = UserFactory.create()
        from pybossa.core import json_exporter as e
        e._make_zip(None, '', 'personal_data', user.dictize(), user.id,
                    'personal_data.zip')

        uri = "/uploads/user_%s/personal_data.zip" % user.id
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))

        # Check only one file in zipfile
        err_msg = "filename count in ZIP is not 1"
        assert len(zip.namelist()) == 1, err_msg
        # Check ZIP filename
        extracted_filename = zip.namelist()[0]
        expected_filename = 'personal_data_.json'
        assert extracted_filename == expected_filename, (zip.namelist()[0],
                                                         expected_filename)
        exported_user = json.loads(zip.read(extracted_filename))
        assert exported_user['id'] == user.id

    @with_context
    def test_export_user_link(self):
        """Test WEB export user data link only for owner."""
        root, user, other = UserFactory.create_batch(3)
        uri = 'account/%s/export' % user.name
        # As anon
        res = self.app.get(uri)
        assert res.status_code == 302

        # As admin
        res = self.app.get(uri + '?api_key=%s' % root.api_key,
                           follow_redirects=True)
        assert res.status_code == 403, res.status_code

        # As other
        res = self.app.get(uri + '?api_key=%s' % other.api_key,
                           follow_redirects=True)
        assert res.status_code == 403, res.status_code

        # As owner
        res = self.app.get(uri + '?api_key=%s' % user.api_key,
                           follow_redirects=True)
        assert res.status_code == 200, res.status_code

        # As non existing user
        uri = 'account/algo/export'
        res = self.app.get(uri + '?api_key=%s' % user.api_key,
                           follow_redirects=True)
        assert res.status_code == 404, res.status_code


    @with_context
    def test_export_user_link_json(self):
        """Test WEB export user data link only for owner as JSON."""
        root, user, other = UserFactory.create_batch(3)
        uri = 'account/%s/export' % user.name
        # As anon
        res = self.app_get_json(uri)
        assert res.status_code == 302

        # As admin
        res = self.app_get_json(uri + '?api_key=%s' % root.api_key,
                                follow_redirects=True)
        assert res.status_code == 403, res.status_code

        # As other
        res = self.app_get_json(uri + '?api_key=%s' % other.api_key,
                                follow_redirects=True)
        assert res.status_code == 403, res.status_code

        # As owner
        res = self.app_get_json(uri + '?api_key=%s' % user.api_key,
                                follow_redirects=True)
        assert res.status_code == 200, res.status_code

        # As non existing user
        uri = 'account/algo/export'
        res = self.app_get_json(uri + '?api_key=%s' % user.api_key,
                                follow_redirects=True)
        assert res.status_code == 404, res.status_code


    @with_context
    @patch('pybossa.exporter.uploader.delete_file')
    @patch('pybossa.exporter.json_export.scheduler.enqueue_in')
    @patch('pybossa.exporter.json_export.uuid.uuid1', return_value='random')
    def test_export_user_json(self, m1, m2, m3):
        """Test export user data in JSON."""
        user = UserFactory.create(id=50423)
        from pybossa.core import json_exporter as e
        e._make_zip(None, '', 'personal_data', user.dictize(), user.id,
                    'personal_data.zip')

        uri = "/uploads/user_%s/random_sec_personal_data.zip" % user.id
        print(uri)
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))

        # Check only one file in zipfile
        err_msg = "filename count in ZIP is not 1"
        assert len(zip.namelist()) == 1, err_msg
        # Check ZIP filename
        extracted_filename = zip.namelist()[0]
        expected_filename = 'personal_data_.json'
        assert extracted_filename == expected_filename, (zip.namelist()[0],
                                                         expected_filename)
        exported_user = json.loads(zip.read(extracted_filename))
        assert exported_user['id'] == user.id

        container = 'user_%s' % user.id
        import datetime
        m2.assert_called_with(datetime.timedelta(3),
                              m3,
                              'random_sec_personal_data.zip',
                              container)

    @with_context
    def test_export_result_json(self):
        """Test WEB export Results to JSON works"""
        project = ProjectFactory.create()
        tasks = TaskFactory.create_batch(5, project=project, n_answers=1)
        for task in tasks:
            TaskRunFactory.create(task=task, project=project)
        results = result_repo.filter_by(project_id=project.id)
        for result in results:
            result.info = dict(key='value')
            result_repo.update(result)

        # First test for a non-existant project
        uri = '/project/somethingnotexists/tasks/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the results in JSON format
        uri = "/project/somethingnotexists/tasks/export?type=result&format=json"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real project
        uri = '/project/%s/tasks/export' % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        assert heading in str(res.data), "Export page should be available\n %s" % res.data
        # Now test that a 404 is raised when an arg is invalid
        uri = "/project/%s/tasks/export?type=ask&format=json" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        uri = "/project/%s/tasks/export?format=json" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        uri = "/project/%s/tasks/export?type=result" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # And a 415 is raised if the requested format is not supported or invalid
        uri = "/project/%s/tasks/export?type=result&format=gson" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '415 UNSUPPORTED MEDIA TYPE', res.status

        # Now get the tasks in JSON format
        self.clear_temp_container(1)   # Project ID 1 is assumed here. See project.id below.
        uri = "/project/%s/tasks/export?type=result&format=json" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))

        # Check only one file in zipfile
        err_msg = "filename count in ZIP is not 1"
        assert len(zip.namelist()) == 1, err_msg
        # Check ZIP filename
        extracted_filename = zip.namelist()[0]
        expected_filename = '%s_result.json' % unidecode(project.short_name)
        assert extracted_filename == expected_filename, (zip.namelist()[0],
                                                         expected_filename)

        exported_results = json.loads(zip.read(extracted_filename))
        assert len(exported_results) == len(results), (len(exported_results),
                                                            len(project.tasks))
        for er in exported_results:
            er['info']['key'] == 'value'
        # Results are exported as an attached file
        content_disposition = 'attachment; filename=%d_%s_result_json.zip' % (project.id,
                                                                              unidecode(project.short_name))
        assert res.headers.get('Content-Disposition') == content_disposition, res.headers


    @with_context
    def test_50_export_task_json(self):
        """Test WEB export Tasks to JSON works"""
        Fixtures.create()
        # First test for a non-existant project
        uri = '/project/somethingnotexists/tasks/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in JSON format
        uri = "/project/somethingnotexists/tasks/export?type=task&format=json"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real project
        uri = '/project/%s/tasks/export' % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        assert heading in str(res.data), "Export page should be available\n %s" % res.data
        # Now test that a 404 is raised when an arg is invalid
        uri = "/project/%s/tasks/export?type=ask&format=json" % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        uri = "/project/%s/tasks/export?format=json" % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        uri = "/project/%s/tasks/export?type=task" % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # And a 415 is raised if the requested format is not supported or invalid
        uri = "/project/%s/tasks/export?type=task&format=gson" % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '415 UNSUPPORTED MEDIA TYPE', res.status

        # Now get the tasks in JSON format
        self.clear_temp_container(1)   # Project ID 1 is assumed here. See project.id below.
        uri = "/project/%s/tasks/export?type=task&format=json" % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))
        # Check only one file in zipfile
        err_msg = "filename count in ZIP is not 1"
        assert len(zip.namelist()) == 1, err_msg
        # Check ZIP filename
        extracted_filename = zip.namelist()[0]
        assert extracted_filename == 'test-app_task.json', zip.namelist()[0]

        exported_tasks = json.loads(zip.read(extracted_filename))
        project = db.session.query(Project)\
            .filter_by(short_name=Fixtures.project_short_name)\
            .first()
        err_msg = "The number of exported tasks is different from Project Tasks"
        assert len(exported_tasks) == len(project.tasks), err_msg
        # Tasks are exported as an attached file
        content_disposition = 'attachment; filename=%d_test-app_task_json.zip' % project.id
        assert res.headers.get('Content-Disposition') == content_disposition, res.headers

    @with_context
    def test_export_task_json_support_non_latin1_project_names(self):
        project = ProjectFactory.create(name='Измени Киев!', short_name='Измени Киев!')
        self.clear_temp_container(project.owner_id)
        res = self.app.get('project/%s/tasks/export?type=task&format=json' % project.short_name,
                           follow_redirects=True)
        filename = secure_filename(unidecode('Измени Киев!'))
        assert filename in res.headers.get('Content-Disposition'), res.headers

    @with_context
    def test_export_taskrun_json_support_non_latin1_project_names(self):
        project = ProjectFactory.create(name='Измени Киев!', short_name='Измени Киев!')
        res = self.app.get('project/%s/tasks/export?type=task_run&format=json' % project.short_name,
                           follow_redirects=True)
        filename = secure_filename(unidecode('Измени Киев!'))
        assert filename in res.headers.get('Content-Disposition'), res.headers

    @with_context
    def test_export_task_csv_support_non_latin1_project_names(self):
        project = ProjectFactory.create(name='Измени Киев!', short_name='Измени Киев!')
        TaskFactory.create(project=project)
        res = self.app.get('/project/%s/tasks/export?type=task&format=csv' % project.short_name,
                           follow_redirects=True)
        filename = secure_filename(unidecode('Измени Киев!'))
        assert filename in res.headers.get('Content-Disposition'), res.headers

    @with_context
    def test_export_taskrun_csv_support_non_latin1_project_names(self):
        project = ProjectFactory.create(name='Измени Киев!', short_name='Измени Киев!')
        task = TaskFactory.create(project=project)
        TaskRunFactory.create(task=task)
        res = self.app.get('/project/%s/tasks/export?type=task_run&format=csv' % project.short_name,
                           follow_redirects=True)
        filename = secure_filename(unidecode('Измени Киев!'))
        assert filename in res.headers.get('Content-Disposition'), res.headers

    @with_context
    def test_export_taskruns_json(self):
        """Test WEB export Task Runs to JSON works"""
        Fixtures.create()
        # First test for a non-existant project
        uri = '/project/somethingnotexists/tasks/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in JSON format
        uri = "/project/somethingnotexists/tasks/export?type=task&format=json"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real project
        self.clear_temp_container(1)   # Project ID 1 is assumed here. See project.id below.
        uri = '/project/%s/tasks/export' % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        assert heading in str(res.data), "Export page should be available\n %s" % res.data
        # Now get the tasks in JSON format
        uri = "/project/%s/tasks/export?type=task_run&format=json" % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))

        # Check only one file in zipfile
        err_msg = "filename count in ZIP is not 1"
        assert len(zip.namelist()) == 1, err_msg
        # Check ZIP filename
        extracted_filename = zip.namelist()[0]
        assert extracted_filename == 'test-app_task_run.json', zip.namelist()[0]

        exported_task_runs = json.loads(zip.read(extracted_filename))
        project = db.session.query(Project)\
                    .filter_by(short_name=Fixtures.project_short_name)\
                    .first()
        err_msg = "The number of exported task runs is different from Project Tasks"
        assert len(exported_task_runs) == len(project.task_runs), err_msg
        # Task runs are exported as an attached file
        content_disposition = 'attachment; filename=%d_test-app_task_run_json.zip' % project.id
        assert res.headers.get('Content-Disposition') == content_disposition, res.headers

    @with_context
    def test_export_task_json_no_tasks_returns_file_with_empty_list(self):
        """Test WEB export Tasks to JSON returns empty list if no tasks in project"""
        project = ProjectFactory.create(short_name='no_tasks_here')
        uri = "/project/%s/tasks/export?type=task&format=json" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))

        extracted_filename = zip.namelist()[0]

        exported_task_runs = json.loads(zip.read(extracted_filename))

        assert exported_task_runs == [], exported_task_runs

    @with_context
    def test_export_result_csv_with_no_keys(self):
        """Test WEB export Results to CSV with no keys works"""
        # First test for a non-existant project
        uri = '/project/somethingnotexists/tasks/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in CSV format
        uri = "/project/somethingnotexists/tasks/export?type=result&format=csv"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the wrong table name in CSV format
        uri = "/project/%s/tasks/export?type=wrong&format=csv" % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real project
        project = ProjectFactory.create()
        self.clear_temp_container(project.owner_id)
        tasks = TaskFactory.create_batch(5, project=project,
                                         n_answers=1)
        for task in tasks:
            TaskRunFactory.create(project=project,
                                  info=[[2001, 1000], [None, None]],
                                  task=task)

        # Get results and update them
        results = result_repo.filter_by(project_id=project.id)
        for result in results:
            result.info = [[2001, 1000], [None, None]]
            result_repo.update(result)

        uri = '/project/%s/tasks/export' % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        data = res.data.decode('utf-8')
        assert heading in str(data), "Export page should be available\n %s" % data
        # Now get the tasks in CSV format
        uri = "/project/%s/tasks/export?type=result&format=csv" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))

        # Check only one file in zipfile
        err_msg = "filename count in ZIP is not 2"
        assert len(zip.namelist()) == 2, err_msg
        # Check ZIP filename
        extracted_filename = zip.namelist()[0]
        assert extracted_filename == 'project1_result.csv', zip.namelist()[0]

        if six.PY2:
            csv_content = StringIO(zip.read(extracted_filename))
        else:
            csv_content = BytesIO(zip.read(extracted_filename))
        csvreader = pd.read_csv(csv_content)
        keys = list(csvreader.columns)
        project = db.session.query(Project)\
                    .filter_by(short_name=project.short_name)\
                    .first()
        err_msg = "The number of exported results is different from Project Results"
        assert csvreader.shape[0] == len(project.tasks), err_msg
        results = db.session.query(Result)\
                    .filter_by(project_id=project.id).all()
        for t in results:
            err_msg = "All the result column names should be included"
            d = t.dictize()
            task_run_ids = d['task_run_ids']
            fl = flatten(t.dictize(), root_keys_to_ignore='task_run_ids')
            fl['task_run_ids'] = task_run_ids
            for tk in list(fl.keys()):
                expected_key = "%s" % tk
                assert expected_key in keys, (err_msg, expected_key, keys)
            err_msg = "All the result.info column names should be included"
            assert type(t.info) == list

        csvreader.fillna('', inplace=True)

        for index, row in csvreader.iterrows():
            et = row
            result_id = et[keys.index('id')]
            result = db.session.query(Result).get(result_id)
            result_dict = result.dictize()
            task_run_ids = result_dict['task_run_ids']
            result_dict_flat = flatten(result_dict,
                                       root_keys_to_ignore='task_run_ids')
            result_dict_flat['task_run_ids'] = task_run_ids
            for k in list(result_dict_flat.keys()):
                slug = '%s' % k
                err_msg = "%s != %s, %s" % (result_dict_flat[k],
                                            et[keys.index(slug)],
                                            k)
                if result_dict_flat[k] is not None:
                    if k == 'task_run_ids':
                        assert '{}'.format(result_dict_flat[k]) == et[keys.index(slug)], err_msg
                    else:
                        assert result_dict_flat[k] == et[keys.index(slug)], err_msg
                else:
                    assert '' == et[keys.index(slug)], err_msg
        # Tasks are exported as an attached file
        content_disposition = 'attachment; filename=%d_project1_result_csv.zip' % project.id
        assert res.headers.get('Content-Disposition') == content_disposition, res.headers

    @with_context
    def test_export_result_csv(self):
        """Test WEB export Results to CSV works"""
        # First test for a non-existant project
        uri = '/project/somethingnotexists/tasks/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in CSV format
        uri = "/project/somethingnotexists/tasks/export?type=result&format=csv"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the wrong table name in CSV format
        uri = "/project/%s/tasks/export?type=wrong&format=csv" % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real project
        project = ProjectFactory.create()
        self.clear_temp_container(project.owner_id)
        tasks = TaskFactory.create_batch(5, project=project,
                                         n_answers=1)
        for task in tasks:
            TaskRunFactory.create(project=project,
                                  info={'question': task.id},
                                  task=task)

        # Get results and update them
        results = result_repo.filter_by(project_id=project.id)
        for result in results:
            result.info = dict(key='value')
            result_repo.update(result)

        uri = '/project/%s/tasks/export' % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        data = res.data.decode('utf-8')
        assert heading in str(data), "Export page should be available\n %s" % data
        # Now get the tasks in CSV format
        uri = "/project/%s/tasks/export?type=result&format=csv" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))

        # Check only one file in zipfile
        err_msg = "filename count in ZIP is not 2"
        assert len(zip.namelist()) == 2, err_msg
        # Check ZIP filename
        extracted_filename = zip.namelist()[0]
        assert extracted_filename == 'project1_result.csv', zip.namelist()[0]

        if six.PY2:
            csv_content = StringIO(zip.read(extracted_filename))
        else:
            csv_content = BytesIO(zip.read(extracted_filename))
        csvreader = pd.read_csv(csv_content)
        project = db.session.query(Project)\
                    .filter_by(short_name=project.short_name)\
                    .first()
        exported_results = []
        err_msg = "The number of exported results is different from Project Results"
        assert csvreader.shape[0] == len(project.tasks), err_msg
        results = db.session.query(Result)\
                    .filter_by(project_id=project.id).all()

        keys = list(csvreader.columns)
        for t in results:
            err_msg = "All the result column names should be included"
            d = t.dictize()
            task_run_ids = d['task_run_ids']
            fl = flatten(t.dictize(), root_keys_to_ignore='task_run_ids')
            fl['task_run_ids'] = task_run_ids
            # keys.append('result_id')
            for tk in list(fl.keys()):
                expected_key = "%s" % tk
                assert expected_key in keys, (err_msg, expected_key, keys)
            err_msg = "All the result.info column names should be included"
            for tk in list(t.info.keys()):
                expected_key = "info_%s" % tk
                assert expected_key in keys, err_msg

        for et in exported_results:
            result_id = et[keys.index('id')]
            result = db.session.query(Result).get(result_id)
            result_dict = result.dictize()
            task_run_ids = result_dict['task_run_ids']
            result_dict_flat = flatten(result_dict,
                                       root_keys_to_ignore='task_run_ids')
            result_dict_flat['task_run_ids'] = task_run_ids
            for k in list(result_dict_flat.keys()):
                slug = '%s' % k
                err_msg = "%s != %s" % (result_dict_flat[k],
                                        et[keys.index(slug)])
                if result_dict_flat[k] is not None:
                    assert str(result_dict_flat[k]) == et[keys.index(slug)], err_msg
                else:
                    assert '' == et[keys.index(slug)], err_msg
            for k in list(result_dict['info'].keys()):
                slug = 'info_%s' % k
                err_msg = "%s != %s" % (result_dict['info'][k], et[keys.index(slug)])
                assert str(result_dict_flat[slug]) == et[keys.index(slug)], err_msg
        # Tasks are exported as an attached file
        content_disposition = 'attachment; filename=%d_project1_result_csv.zip' % project.id
        assert res.headers.get('Content-Disposition') == content_disposition, res.headers

    @with_context
    def test_export_task_csv_ignore_keys(self):
        """Test WEB export Tasks to CSV with ignore keys works"""
        # First test for a non-existant project
        with patch.dict(self.flask_app.config, {'IGNORE_FLAT_KEYS': ['geojson']}):
            uri = '/project/somethingnotexists/tasks/export'
            res = self.app.get(uri, follow_redirects=True)
            assert res.status == '404 NOT FOUND', res.status
            # Now get the tasks in CSV format
            uri = "/project/somethingnotexists/tasks/export?type=task&format=csv"
            res = self.app.get(uri, follow_redirects=True)
            assert res.status == '404 NOT FOUND', res.status
            # Now get the wrong table name in CSV format
            uri = "/project/%s/tasks/export?type=wrong&format=csv" % Fixtures.project_short_name
            res = self.app.get(uri, follow_redirects=True)
            assert res.status == '404 NOT FOUND', res.status

            # Now with a real project
            project = ProjectFactory.create()
            self.clear_temp_container(project.owner_id)

            TaskFactory.create_batch(5, project=project, info={'question': 'qu',
                                                               'geojson':
                                                               'complexjson'})
            # Empty task that should be handled as well.
            TaskFactory.create(project=project, info=None)
            uri = '/project/%s/tasks/export' % project.short_name
            res = self.app.get(uri, follow_redirects=True)
            heading = "Export All Tasks and Task Runs"
            data = res.data.decode('utf-8')
            assert heading in str(data), "Export page should be available\n %s" % data
            # Now get the tasks in CSV format
            uri = "/project/%s/tasks/export?type=task&format=csv" % project.short_name
            res = self.app.get(uri, follow_redirects=True)
            if six.PY2:
                zip = zipfile.ZipFile(StringIO(str(res.data)))
            else:
                zip = zipfile.ZipFile(BytesIO(res.data))

            # Check only one file in zipfile
            err_msg = "filename count in ZIP is not 2"
            assert len(zip.namelist()) == 2, err_msg
            # Check ZIP filename
            extracted_filename = zip.namelist()[0]
            assert extracted_filename == 'project1_task.csv', zip.namelist()[0]

            csv_content = zip.read(extracted_filename)
            if six.PY2:
                csv_content = StringIO(csv_content)
            else:
                csv_content = BytesIO(csv_content)
            csvreader = pd.read_csv(csv_content)
            csvreader.fillna('', inplace=True)
            project = db.session.query(Project)\
                        .filter_by(short_name=project.short_name)\
                        .first()
            keys = list(csvreader.columns)
            err_msg = "The number of exported tasks is different from Project Tasks"
            assert csvreader.shape[0] == len(project.tasks), err_msg
            for t in project.tasks:
                err_msg = "All the task column names should be included"
                d = copy.deepcopy(t.dictize())
                if d['info']:
                    d['info'].pop('geojson', None)
                for tk in list(flatten(d).keys()):
                    expected_key = "%s" % tk
                    assert expected_key in keys, (expected_key, err_msg)
                err_msg = "All the task.info column names should be included except geojson"
                info_keys = None
                if t.info:
                    info_keys = copy.deepcopy(list(t.info.keys()))
                    info_keys.pop(info_keys.index('geojson'))
                    for tk in info_keys:
                        expected_key = "info_%s" % tk
                        assert expected_key in keys, (expected_key, err_msg)

            for index, et in csvreader.iterrows():
                task_id = et[keys.index('id')]
                task = db.session.query(Task).get(task_id)
                task_dict = copy.deepcopy(task.dictize())
                if task_dict['info']:
                    task_dict['info'].pop('geojson', None)
                    task_dict_flat = copy.deepcopy(flatten(task_dict))
                    for k in list(task_dict_flat.keys()):
                        slug = '%s' % k
                        err_msg = "%s != %s, %s" % (task_dict_flat[k],
                                                    et[keys.index(slug)], k)
                        if task_dict_flat[k] is not None:
                            assert task_dict_flat[k] == et[keys.index(slug)], err_msg
                        else:
                            assert '' == et[keys.index(slug)], err_msg
                    for k in list(task_dict['info'].keys()):
                        slug = 'info_%s' % k
                        err_msg = "%s != %s" % (task_dict['info'][k], et[keys.index(slug)])
                        assert str(task_dict_flat[slug]) == et[keys.index(slug)], err_msg
            # Tasks are exported as an attached file
            content_disposition = 'attachment; filename=%d_project1_task_csv.zip' % project.id
            assert res.headers.get('Content-Disposition') == content_disposition, res.headers


    @with_context
    def test_export_task_csv_new_root_key_without_keys(self):
        """Test WEB export Tasks to CSV new root key without keys works"""
        # Fixtures.create()
        # First test for a non-existant project
        with patch.dict(self.flask_app.config, {'TASK_CSV_EXPORT_INFO_KEY':'answer'}):
            uri = '/project/somethingnotexists/tasks/export'
            res = self.app.get(uri, follow_redirects=True)
            assert res.status == '404 NOT FOUND', res.status
            # Now get the tasks in CSV format
            uri = "/project/somethingnotexists/tasks/export?type=task&format=csv"
            res = self.app.get(uri, follow_redirects=True)
            assert res.status == '404 NOT FOUND', res.status
            # Now get the wrong table name in CSV format
            uri = "/project/%s/tasks/export?type=wrong&format=csv" % Fixtures.project_short_name
            res = self.app.get(uri, follow_redirects=True)
            assert res.status == '404 NOT FOUND', res.status

            # Now with a real project
            project = ProjectFactory.create()
            self.clear_temp_container(project.owner_id)
            for i in range(0, 5):
                task = TaskFactory.create(project=project,
                                          info=[[1,2]])
            uri = '/project/%s/tasks/export' % project.short_name

            res = self.app.get(uri, follow_redirects=True)
            heading = "Export All Tasks and Task Runs"
            data = res.data.decode('utf-8')
            assert heading in str(data), "Export page should be available\n %s" % data
            # Now get the tasks in CSV format
            uri = "/project/%s/tasks/export?type=task&format=csv" % project.short_name
            res = self.app.get(uri, follow_redirects=True)
            file_name = '/tmp/task_%s.zip' % project.short_name
            if six.PY2:
                with open(file_name, 'w') as f:
                    f.write(res.data)
            else:
                with open(file_name, 'w+b') as f:
                    f.write(res.data)
            zip = zipfile.ZipFile(file_name)
            zip.extractall('/tmp')
            # Check only one file in zipfile
            err_msg = "filename count in ZIP is not 2"
            assert len(zip.namelist()) == 2, err_msg
            # Check ZIP filename
            extracted_filename = zip.namelist()[1]
            assert extracted_filename == 'project1_task_info_only.csv', zip.namelist()[1]

            csv_content = codecs.open('/tmp/' + extracted_filename, 'r', 'utf-8')

            project = db.session.query(Project)\
                        .filter_by(short_name=project.short_name)\
                        .first()
            exported_tasks = []
            assert_raises(EmptyDataError, pd.read_csv, csv_content)
            err_msg = "The number of exported tasks should be 0 as there are no keys"
            # Tasks are exported as an attached file
            content_disposition = 'attachment; filename=%d_project1_task_csv.zip' % project.id
            assert res.headers.get('Content-Disposition') == content_disposition, res.headers



    @with_context
    def test_export_task_csv_new_root_key(self):
        """Test WEB export Tasks to CSV new root key works"""
        # Fixtures.create()
        # First test for a non-existant project
        with patch.dict(self.flask_app.config, {'TASK_CSV_EXPORT_INFO_KEY':'answer'}):
            uri = '/project/somethingnotexists/tasks/export'
            res = self.app.get(uri, follow_redirects=True)
            assert res.status == '404 NOT FOUND', res.status
            # Now get the tasks in CSV format
            uri = "/project/somethingnotexists/tasks/export?type=task&format=csv"
            res = self.app.get(uri, follow_redirects=True)
            assert res.status == '404 NOT FOUND', res.status
            # Now get the wrong table name in CSV format
            uri = "/project/%s/tasks/export?type=wrong&format=csv" % Fixtures.project_short_name
            res = self.app.get(uri, follow_redirects=True)
            assert res.status == '404 NOT FOUND', res.status

            # Now with a real project
            project = ProjectFactory.create()
            self.clear_temp_container(project.owner_id)
            for i in range(0, 5):
                task = TaskFactory.create(project=project,
                                          info={'answer':[{'eñe': i}]})
            uri = '/project/%s/tasks/export' % project.short_name

            res = self.app.get(uri, follow_redirects=True)
            heading = "Export All Tasks and Task Runs"
            data = res.data.decode('utf-8')
            assert heading in str(data), "Export page should be available\n %s" % data
            # Now get the tasks in CSV format
            uri = "/project/%s/tasks/export?type=task&format=csv" % project.short_name
            res = self.app.get(uri, follow_redirects=True)
            file_name = '/tmp/task_%s.zip' % project.short_name
            if six.PY2:
                with open(file_name, 'w') as f:
                    f.write(res.data)
            else:
                with open(file_name, 'w+b') as f:
                    f.write(res.data)
            zip = zipfile.ZipFile(file_name, 'r')
            zip.extractall('/tmp')
            # Check only one file in zipfile
            err_msg = "filename count in ZIP is not 2"
            assert len(zip.namelist()) == 2, err_msg
            # Check ZIP filename
            extracted_filename = zip.namelist()[1]
            assert extracted_filename == 'project1_task_info_only.csv', zip.namelist()[1]

            csv_content = codecs.open('/tmp/' + extracted_filename, 'r', 'utf-8')

            csvreader = pd.read_csv(csv_content)
            project = db.session.query(Project)\
                        .filter_by(short_name=project.short_name)\
                        .first()

            assert csvreader.shape[0] == len(project.tasks), (err_msg,
                                                              len(exported_tasks),
                                                              len(project.tasks))
            keys = list(csvreader.columns)
            for t in project.tasks:
                err_msg = "All the task column names should be included"
                for tk in list(flatten(t.info['answer'][0]).keys()):
                    expected_key = "%s" % tk
                    assert expected_key in keys, (expected_key, err_msg)

            for index, et in csvreader.iterrows():
                et = list(et)
                task_id = et[keys.index('task_id')]
                task = db.session.query(Task).get(task_id)
                task_dict_flat = flatten(task.info['answer'][0])
                task_dict = task.dictize()
                for k in list(task_dict_flat.keys()):
                    slug = '%s' % k
                    err_msg = "%s != %s" % (task_dict_flat[k], et[keys.index(slug)])
                    if task_dict_flat[k] is not None:
                        assert task_dict_flat[k] == et[keys.index(slug)], err_msg
                    else:
                        assert '' == et[keys.index(slug)], err_msg
                for datum in task_dict['info']['answer']:
                    for k in list(datum.keys()):
                        slug = '%s' % k
                        assert task_dict_flat[slug] == et[keys.index(slug)], err_msg
            # Tasks are exported as an attached file
            content_disposition = 'attachment; filename=%d_project1_task_csv.zip' % project.id
            assert res.headers.get('Content-Disposition') == content_disposition, res.headers


    @with_context
    def test_export_task_csv(self):
        """Test WEB export Tasks to CSV works"""
        # Fixtures.create()
        # First test for a non-existant project
        uri = '/project/somethingnotexists/tasks/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in CSV format
        uri = "/project/somethingnotexists/tasks/export?type=task&format=csv"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the wrong table name in CSV format
        uri = "/project/%s/tasks/export?type=wrong&format=csv" % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real project
        project = ProjectFactory.create()
        self.clear_temp_container(project.owner_id)
        for i in range(0, 5):
            task = TaskFactory.create(project=project, info={'eñe': i})
        uri = '/project/%s/tasks/export' % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        data = res.data.decode('utf-8')
        assert heading in str(data), "Export page should be available\n %s" % data
        # Now get the tasks in CSV format
        uri = "/project/%s/tasks/export?type=task&format=csv" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        file_name = '/tmp/task_%s.zip' % project.short_name
        if six.PY2:
            with open(file_name, 'w') as f:
                f.write(res.data)
        else:
            with open(file_name, 'w+b') as f:
                f.write(res.data)
        zip = zipfile.ZipFile(file_name, 'r')
        zip.extractall('/tmp')
        # Check only one file in zipfile
        err_msg = "filename count in ZIP is not 2"
        assert len(zip.namelist()) == 2, err_msg
        # Check ZIP filename
        extracted_filename = zip.namelist()[0]
        assert extracted_filename == 'project1_task.csv', zip.namelist()[0]

        csv_content = codecs.open('/tmp/' + extracted_filename, 'r', 'utf-8')

        csvreader = pd.read_csv(csv_content)
        project = db.session.query(Project)\
                    .filter_by(short_name=project.short_name)\
                    .first()
        exported_tasks = []
        keys = list(csvreader.columns)
        assert csvreader.shape[0] == len(project.tasks), (err_msg,
                                                           len(exported_tasks),
                                                           len(project.tasks))
        for t in project.tasks:
            err_msg = "All the task column names should be included"
            for tk in list(flatten(t.dictize()).keys()):
                expected_key = "%s" % tk
                assert expected_key in keys, (expected_key, err_msg)
            err_msg = "All the task.info column names should be included"
            for tk in list(t.info.keys()):
                expected_key = "info_%s" % tk
                assert expected_key in keys, (err_msg, expected_key, keys)

        for et in exported_tasks:
            task_id = et[keys.index('id')]
            task = db.session.query(Task).get(task_id)
            task_dict_flat = flatten(task.dictize())
            task_dict = task.dictize()
            for k in list(task_dict_flat.keys()):
                slug = '%s' % k
                err_msg = "%s != %s" % (task_dict_flat[k], et[keys.index(slug)])
                if task_dict_flat[k] is not None:
                    assert str(task_dict_flat[k]) == et[keys.index(slug)], err_msg
                else:
                    assert '' == et[keys.index(slug)], err_msg
            for k in list(task_dict['info'].keys()):
                slug = 'info_%s' % k
                err_msg = "%s != %s" % (task_dict['info'][k], et[keys.index(slug)])
                assert str(task_dict_flat[slug]) == et[keys.index(slug)], err_msg
        # Tasks are exported as an attached file
        content_disposition = 'attachment; filename=%d_project1_task_csv.zip' % project.id
        assert res.headers.get('Content-Disposition') == content_disposition, res.headers

    @with_context
    def test_export_result_csv_no_tasks_returns_empty_file(self):
        """Test WEB export Result to CSV returns empty file if no results in
        project."""
        project = ProjectFactory.create(short_name='no_tasks_here')
        uri = "/project/%s/tasks/export?type=result&format=csv" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))
        extracted_filename = zip.namelist()[0]

        if six.PY2:
            csv_content = StringIO(zip.read(extracted_filename))
        else:
            csv_content = BytesIO(zip.read(extracted_filename))
        assert_raises(EmptyDataError, pd.read_csv, csv_content)

    @with_context
    def test_export_task_csv_no_tasks_returns_empty_file(self):
        """Test WEB export Tasks to CSV returns empty file if no tasks in project"""
        project = ProjectFactory.create(short_name='no_tasks_here')
        uri = "/project/%s/tasks/export?type=task&format=csv" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))
        extracted_filename = zip.namelist()[0]

        if six.PY2:
            csv_content = StringIO(zip.read(extracted_filename))
        else:
            csv_content = BytesIO(zip.read(extracted_filename))
        assert_raises(EmptyDataError, pd.read_csv, csv_content)

    @with_context
    def test_53_export_task_runs_csv(self):
        """Test WEB export Task Runs to CSV works"""
        # First test for a non-existant project
        uri = '/project/somethingnotexists/tasks/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in CSV format
        uri = "/project/somethingnotexists/tasks/export?type=tas&format=csv"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real project
        project = ProjectFactory.create()
        self.clear_temp_container(project.owner_id)
        task = TaskFactory.create(project=project)
        for i in range(2):
            task_run = TaskRunFactory.create(project=project, task=task, info={'answer': i})
        uri = '/project/%s/tasks/export' % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        data = res.data.decode('utf-8')
        assert heading in str(data), "Export page should be available\n %s" % data
        # Now get the tasks in CSV format
        uri = "/project/%s/tasks/export?type=task_run&format=csv" % project.short_name
        res = self.app.get(uri, follow_redirects=True)
        if six.PY2:
            zip = zipfile.ZipFile(StringIO(str(res.data)))
        else:
            zip = zipfile.ZipFile(BytesIO(res.data))

        # Check only one file in zipfile
        err_msg = "filename count in ZIP is not 2"
        assert len(zip.namelist()) == 2, err_msg
        # Check ZIP filename
        extracted_filename = zip.namelist()[0]
        print(extracted_filename)
        assert extracted_filename == 'project1_task_run.csv', zip.namelist()[0]
        extracted_filename_info_only = zip.namelist()[1]
        assert extracted_filename_info_only == 'project1_task_run_info_only.csv', zip.namelist()[1]
        zip_data = zip.read(str(extracted_filename))
        csv_content = StringIO(zip_data.decode('utf-8'))
        csv_df = pd.read_csv(csv_content)
        project = db.session.query(Project)\
            .filter_by(short_name=project.short_name)\
            .first()
        exported_task_runs = []
        assert csv_df.shape[0] == len(project.task_runs), err_msg

        keys = list(csv_df.columns)

        for t in project.tasks[0].task_runs:
            for tk in list(flatten(t.dictize()).keys()):
                expected_key = "%s" % tk
                assert expected_key in keys, expected_key

        for et in exported_task_runs:
            task_run_id = et[keys.index('id')]
            task_run = db.session.query(TaskRun).get(task_run_id)
            task_run_dict = flatten(task_run.dictize())
            for k in task_run_dict:
                slug = '%s' % k
                err_msg = "%s != %s" % (task_run_dict[k], et[keys.index(slug)])
                if task_run_dict[k] is not None:
                    assert str(task_run_dict[k]) == et[keys.index(slug)], err_msg
                else:
                    assert '' == et[keys.index(slug)], err_msg
        # Task runs are exported as an attached file
        content_disposition = 'attachment; filename=%d_project1_task_run_csv.zip' % project.id
        assert res.headers.get('Content-Disposition') == content_disposition, res.headers

    @with_context
    @patch('pybossa.view.projects.Ckan', autospec=True)
    def test_export_tasks_ckan_exception(self, mock1):
        mocks = [Mock()]
        from test_ckan import TestCkanModule
        fake_ckn = TestCkanModule()
        package = fake_ckn.pkg_json_found
        package['id'] = 3
        mocks[0].package_exists.return_value = (False,
                                                Exception("CKAN: error",
                                                          "error", 500))
        # mocks[0].package_create.return_value = fake_ckn.pkg_json_found
        # mocks[0].resource_create.return_value = dict(result=dict(id=3))
        # mocks[0].datastore_create.return_value = 'datastore'
        # mocks[0].datastore_upsert.return_value = 'datastore'

        mock1.side_effect = mocks

        """Test WEB Export CKAN Tasks works."""
        Fixtures.create()
        user = db.session.query(User).filter_by(name=Fixtures.name).first()
        project = db.session.query(Project).first()
        user.ckan_api = 'ckan-api-key'
        project.owner_id = user.id
        db.session.add(user)
        db.session.add(project)
        db.session.commit()

        self.signin(email=user.email_addr, password=Fixtures.password)
        # Now with a real project
        uri = '/project/%s/tasks/export' % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        assert heading in str(res.data), "Export page should be available\n %s" % res.data
        # Now get the tasks in CKAN format
        uri = "/project/%s/tasks/export?type=task&format=ckan" % Fixtures.project_short_name
        with patch.dict(self.flask_app.config, {'CKAN_URL': 'http://ckan.com'}):
            # First time exporting the package
            res = self.app.get(uri, follow_redirects=True)
            msg = 'Error'
            err_msg = "An exception should be raised"
            assert msg in str(res.data), err_msg

    @with_context
    @patch('pybossa.view.projects.Ckan', autospec=True)
    def test_export_tasks_ckan_connection_error(self, mock1):
        mocks = [Mock()]
        from test_ckan import TestCkanModule
        fake_ckn = TestCkanModule()
        package = fake_ckn.pkg_json_found
        package['id'] = 3
        mocks[0].package_exists.return_value = (False, ConnectionError)
        # mocks[0].package_create.return_value = fake_ckn.pkg_json_found
        # mocks[0].resource_create.return_value = dict(result=dict(id=3))
        # mocks[0].datastore_create.return_value = 'datastore'
        # mocks[0].datastore_upsert.return_value = 'datastore'

        mock1.side_effect = mocks

        """Test WEB Export CKAN Tasks works."""
        Fixtures.create()
        user = db.session.query(User).filter_by(name=Fixtures.name).first()
        project = db.session.query(Project).first()
        user.ckan_api = 'ckan-api-key'
        project.owner_id = user.id
        db.session.add(user)
        db.session.add(project)
        db.session.commit()

        self.signin(email=user.email_addr, password=Fixtures.password)
        # Now with a real project
        uri = '/project/%s/tasks/export' % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        assert heading in str(res.data), "Export page should be available\n %s" % res.data
        # Now get the tasks in CKAN format
        uri = "/project/%s/tasks/export?type=task&format=ckan" % Fixtures.project_short_name
        with patch.dict(self.flask_app.config, {'CKAN_URL': 'http://ckan.com'}):
            # First time exporting the package
            res = self.app.get(uri, follow_redirects=True)
            msg = 'CKAN server seems to be down'
            err_msg = "A connection exception should be raised"
            assert msg in str(res.data), err_msg

    @with_context
    @patch('pybossa.view.projects.Ckan', autospec=True)
    def test_task_export_tasks_ckan_first_time(self, mock1):
        """Test WEB Export CKAN Tasks works without an existing package."""
        # Second time exporting the package
        mocks = [Mock()]
        resource = dict(name='task', id=1)
        package = dict(id=3, resources=[resource])
        mocks[0].package_exists.return_value = (None, None)
        mocks[0].package_create.return_value = package
        #mocks[0].datastore_delete.return_value = None
        mocks[0].datastore_create.return_value = None
        mocks[0].datastore_upsert.return_value = None
        mocks[0].resource_create.return_value = dict(result=dict(id=3))
        mocks[0].datastore_create.return_value = 'datastore'
        mocks[0].datastore_upsert.return_value = 'datastore'

        mock1.side_effect = mocks

        Fixtures.create()
        user = db.session.query(User).filter_by(name=Fixtures.name).first()
        project = db.session.query(Project).first()
        user.ckan_api = 'ckan-api-key'
        project.owner_id = user.id
        db.session.add(user)
        db.session.add(project)
        db.session.commit()

        self.signin(email=user.email_addr, password=Fixtures.password)
        # First test for a non-existant project
        uri = '/project/somethingnotexists/tasks/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in CKAN format
        uri = "/project/somethingnotexists/tasks/export?type=task&format=ckan"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in CKAN format
        uri = "/project/somethingnotexists/tasks/export?type=other&format=ckan"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real project
        uri = '/project/%s/tasks/export' % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        assert heading in str(res.data), "Export page should be available\n %s" % res.data
        # Now get the tasks in CKAN format
        uri = "/project/%s/tasks/export?type=task&format=ckan" % Fixtures.project_short_name
        with patch.dict(self.flask_app.config, {'CKAN_URL': 'http://ckan.com'}):
            # First time exporting the package
            res = self.app.get(uri, follow_redirects=True)
            msg = 'Data exported to http://ckan.com'
            err_msg = "Tasks should be exported to CKAN"
            assert msg in str(res.data), err_msg

    @with_context
    @patch('pybossa.view.projects.Ckan', autospec=True)
    def test_task_export_tasks_ckan_second_time(self, mock1):
        """Test WEB Export CKAN Tasks works with an existing package."""
        # Second time exporting the package
        mocks = [Mock()]
        resource = dict(name='task', id=1)
        package = dict(id=3, resources=[resource])
        mocks[0].package_exists.return_value = (package, None)
        mocks[0].package_update.return_value = package
        mocks[0].datastore_delete.return_value = None
        mocks[0].datastore_create.return_value = None
        mocks[0].datastore_upsert.return_value = None
        mocks[0].resource_create.return_value = dict(result=dict(id=3))
        mocks[0].datastore_create.return_value = 'datastore'
        mocks[0].datastore_upsert.return_value = 'datastore'

        mock1.side_effect = mocks

        Fixtures.create()
        user = db.session.query(User).filter_by(name=Fixtures.name).first()
        project = db.session.query(Project).first()
        user.ckan_api = 'ckan-api-key'
        project.owner_id = user.id
        db.session.add(user)
        db.session.add(project)
        db.session.commit()

        self.signin(email=user.email_addr, password=Fixtures.password)
        # First test for a non-existant project
        uri = '/project/somethingnotexists/tasks/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in CKAN format
        uri = "/project/somethingnotexists/tasks/export?type=task&format=ckan"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real project
        uri = '/project/%s/tasks/export' % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        assert heading in str(res.data), "Export page should be available\n %s" % res.data
        # Now get the tasks in CKAN format
        uri = "/project/%s/tasks/export?type=task&format=ckan" % Fixtures.project_short_name
        #res = self.app.get(uri, follow_redirects=True)
        with patch.dict(self.flask_app.config, {'CKAN_URL': 'http://ckan.com'}):
            # First time exporting the package
            res = self.app.get(uri, follow_redirects=True)
            msg = 'Data exported to http://ckan.com'
            err_msg = "Tasks should be exported to CKAN"
            assert msg in str(res.data), err_msg

    @with_context
    @patch('pybossa.view.projects.Ckan', autospec=True)
    def test_task_export_tasks_ckan_without_resources(self, mock1):
        """Test WEB Export CKAN Tasks works without resources."""
        mocks = [Mock()]
        package = dict(id=3, resources=[])
        mocks[0].package_exists.return_value = (package, None)
        mocks[0].package_update.return_value = package
        mocks[0].resource_create.return_value = dict(result=dict(id=3))
        mocks[0].datastore_create.return_value = 'datastore'
        mocks[0].datastore_upsert.return_value = 'datastore'

        mock1.side_effect = mocks

        Fixtures.create()
        user = db.session.query(User).filter_by(name=Fixtures.name).first()
        project = db.session.query(Project).first()
        user.ckan_api = 'ckan-api-key'
        project.owner_id = user.id
        db.session.add(user)
        db.session.add(project)
        db.session.commit()

        self.signin(email=user.email_addr, password=Fixtures.password)
        # First test for a non-existant project
        uri = '/project/somethingnotexists/tasks/export'
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status
        # Now get the tasks in CKAN format
        uri = "/project/somethingnotexists/tasks/export?type=task&format=ckan"
        res = self.app.get(uri, follow_redirects=True)
        assert res.status == '404 NOT FOUND', res.status

        # Now with a real project
        uri = '/project/%s/tasks/export' % Fixtures.project_short_name
        res = self.app.get(uri, follow_redirects=True)
        heading = "Export All Tasks and Task Runs"
        assert heading in str(res.data), "Export page should be available\n %s" % res.data
        # Now get the tasks in CKAN format
        uri = "/project/%s/tasks/export?type=task&format=ckan" % Fixtures.project_short_name
        #res = self.app.get(uri, follow_redirects=True)
        with patch.dict(self.flask_app.config, {'CKAN_URL': 'http://ckan.com'}):
            # First time exporting the package
            res = self.app.get(uri, follow_redirects=True)
            msg = 'Data exported to http://ckan.com'
            err_msg = "Tasks should be exported to CKAN"
            assert msg in str(res.data), err_msg

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_get_import_tasks_no_params_shows_options_and_templates(self, mock):
        """Test WEB import tasks displays the different importers and template
        tasks"""
        Fixtures.create()
        self.register()
        self.new_project()
        res = self.app.get('/project/sampleapp/tasks/import', follow_redirects=True)
        err_msg = "There should be a CSV importer"
        assert "type=csv" in str(res.data), err_msg
        err_msg = "There should be a GDocs importer"
        assert "type=gdocs" in str(res.data), err_msg
        err_msg = "There should be an Epicollect importer"
        assert "type=epicollect" in str(res.data), err_msg
        err_msg = "There should be a Flickr importer"
        assert "type=flickr" in str(res.data), err_msg
        err_msg = "There should be a Dropbox importer"
        assert "type=dropbox" in str(res.data), err_msg
        err_msg = "There should be a Twitter importer"
        assert "type=twitter" in str(res.data), err_msg
        err_msg = "There should be an S3 importer"
        assert "type=s3" in str(res.data), err_msg
        err_msg = "There should be an Image template"
        assert "template=image" in str(res.data), err_msg
        err_msg = "There should be a Map template"
        assert "template=map" in str(res.data), err_msg
        err_msg = "There should be a PDF template"
        assert "template=pdf" in str(res.data), err_msg
        err_msg = "There should be a Sound template"
        assert "template=sound" in str(res.data), err_msg
        err_msg = "There should be a Video template"
        assert "template=video" in str(res.data), err_msg

        self.signout()

        self.signin(email=Fixtures.email_addr2, password=Fixtures.password)
        res = self.app.get('/project/sampleapp/tasks/import', follow_redirects=True)
        assert res.status_code == 403, res.status_code

    @with_context
    @patch('pybossa.view.projects.importer.create_tasks')
    @patch('pybossa.view.projects.importer.count_tasks_to_import', return_value=1)
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_get_import_tasks_no_params_shows_options_and_templates_json_owner(self, mock, importer_count, importer_tasks):
        """Test WEB import tasks JSON returns tasks's templates """
        admin, user, owner = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        report = MagicMock()
        report.message = "SUCCESS"
        importer_tasks.return_value = report
        url = '/project/%s/tasks/import?api_key=%s' % (project.short_name, owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)

        assert data['available_importers'] is not None, data
        importers = ["projects/tasks/epicollect.html",
                     "projects/tasks/csv.html",
                     "projects/tasks/s3.html",
                     "projects/tasks/twitter.html",
                     "projects/tasks/youtube.html",
                     "projects/tasks/gdocs.html",
                     "projects/tasks/dropbox.html",
                     "projects/tasks/flickr.html",
                     "projects/tasks/localCSV.html",
                     "projects/tasks/iiif.html"]
        assert sorted(data['available_importers']) == sorted(importers), data

        importers = ['&type=epicollect',
                     '&type=csv',
                     '&type=s3',
                     '&type=twitter',
                     '&type=youtube',
                     '&type=gdocs',
                     '&type=dropbox',
                     '&type=flickr',
                     '&type=localCSV',
                     '&type=iiif']

        for importer in importers:
            res = self.app_get_json(url + importer)
            data = json.loads(res.data)
            assert data['form']['csrf'] is not None
            if 'epicollect' in importer:
                assert 'epicollect_form' in list(data['form'].keys()), data
                assert 'epicollect_project' in list(data['form'].keys()), data
            if 'csv' in importer:
                assert 'csv_url' in list(data['form'].keys()), data
            if importer == 's3':
                assert 'files' in list(data['form'].keys()), data
                assert 'bucket' in list(data['form'].keys()), data
            if 'twitter' in importer:
                assert 'max_tweets' in list(data['form'].keys()), data
                assert 'source' in list(data['form'].keys()), data
                assert 'user_credentials' in list(data['form'].keys()), data
            if 'youtube' in importer:
                assert 'playlist_url' in list(data['form'].keys()), data
            if 'gdocs' in importer:
                assert 'googledocs_url' in list(data['form'].keys()), data
            if 'dropbox' in importer:
                assert 'files' in list(data['form'].keys()), data
            if 'flickr' in importer:
                assert 'album_id' in list(data['form'].keys()), data
            if 'localCSV' in importer:
                assert 'form_name' in list(data['form'].keys()), data
            if 'iiif' in importer:
                assert 'manifest_uri' in list(data['form'].keys()), data

        for importer in importers:
            if 'epicollect' in importer:
                data = dict(epicollect_form='data', epicollect_project='project')
                res = self.app_post_json(url + importer, data=data)
                data = json.loads(res.data)
                assert data['flash'] == "SUCCESS", data
            if 'csv' in importer:
                data = dict(csv_url='http://data.com')
                res = self.app_post_json(url + importer, data=data)
                data = json.loads(res.data)
                print(data)
                assert data['flash'] == "SUCCESS", data
            if 's3' in importer:
                data = dict(files='data', bucket='bucket')
                res = self.app_post_json(url + importer, data=data)
                data = json.loads(res.data)
                assert data['flash'] == "SUCCESS", data
            if 'twitter' in importer:
                data = dict(max_tweets=1, source='bucket', user_credentials='user')
                res = self.app_post_json(url + importer, data=data)
                data = json.loads(res.data)
                assert data['flash'] == "SUCCESS", data
            if 'youtube' in importer:
                data = dict(playlist_url='url')
                res = self.app_post_json(url + importer, data=data)
                data = json.loads(res.data)
                assert data['flash'] == "SUCCESS", data
            if 'gdocs' in importer:
                data = dict(googledocs_url='http://url.com')
                res = self.app_post_json(url + importer, data=data)
                data = json.loads(res.data)
                assert data['flash'] == "SUCCESS", data
            if 'dropbox' in importer:
                data = dict(files='http://domain.com')
                res = self.app_post_json(url + importer, data=data)
                data = json.loads(res.data)
                assert data['flash'] == "SUCCESS", data
            if 'flickr' in importer:
                data = dict(album_id=13)
                res = self.app_post_json(url + importer, data=data)
                data = json.loads(res.data)
                assert data['flash'] == "SUCCESS", data
            if 'iiif' in importer:
                data = dict(manifest_uri='http://example.com')
                res = self.app_post_json(url + importer, data=data)
                data = json.loads(res.data)
                assert data['flash'] == "SUCCESS", data


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_get_import_tasks_no_params_shows_options_and_templates_json_admin(self, mock):
        """Test WEB import tasks JSON returns tasks's templates """
        admin, user, owner = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)

        url = '/project/%s/tasks/import?api_key=%s' % (project.short_name, admin.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)

        assert data['available_importers'] is not None, data
        importers = ["projects/tasks/epicollect.html",
                     "projects/tasks/csv.html",
                     "projects/tasks/s3.html",
                     "projects/tasks/twitter.html",
                     "projects/tasks/youtube.html",
                     "projects/tasks/gdocs.html",
                     "projects/tasks/dropbox.html",
                     "projects/tasks/flickr.html",
                     "projects/tasks/localCSV.html",
                     "projects/tasks/iiif.html"]
        assert sorted(data['available_importers']) == sorted(importers), (importers,
                                                          data['available_importers'])


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_get_import_tasks_no_params_shows_options_and_templates_json_user(self, mock):
        """Test WEB import tasks JSON returns tasks's templates """
        admin, user, owner = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)

        url = '/project/%s/tasks/import?api_key=%s' % (project.short_name, user.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert data['code'] == 403, data

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_get_import_tasks_no_params_shows_options_and_templates_json_anon(self, mock):
        """Test WEB import tasks JSON returns tasks's templates """
        admin, user, owner = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)

        url = '/project/%s/tasks/import' % (project.short_name)
        res = self.app_get_json(url, follow_redirects=True)
        assert 'signin' in str(res.data), res.data


    @with_context
    def test_get_import_tasks_with_specific_variant_argument(self):
        """Test task importer with specific importer variant argument
        shows the form for it, for each of the variants"""
        self.register()
        owner = db.session.query(User).first()
        project = ProjectFactory.create(owner=owner)

        # CSV
        url = "/project/%s/tasks/import?type=csv" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From a CSV file" in data
        assert 'action="/project/%E2%9C%93project1/tasks/import"' in data

        # Google Docs
        url = "/project/%s/tasks/import?type=gdocs" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From a Google Docs Spreadsheet" in data
        assert 'action="/project/%E2%9C%93project1/tasks/import"' in data

        # Epicollect Plus
        url = "/project/%s/tasks/import?type=epicollect" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From an EpiCollect Plus project" in data
        assert 'action="/project/%E2%9C%93project1/tasks/import"' in data

        # Flickr
        url = "/project/%s/tasks/import?type=flickr" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From a Flickr Album" in data
        assert 'action="/project/%E2%9C%93project1/tasks/import"' in data

        # Dropbox
        url = "/project/%s/tasks/import?type=dropbox" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From your Dropbox account" in data
        assert 'action="/project/%E2%9C%93project1/tasks/import"' in data

        # Twitter
        url = "/project/%s/tasks/import?type=twitter" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From a Twitter hashtag or account" in data
        assert 'action="/project/%E2%9C%93project1/tasks/import"' in data

        # S3
        url = "/project/%s/tasks/import?type=s3" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From an Amazon S3 bucket" in data
        assert 'action="/project/%E2%9C%93project1/tasks/import"' in data

        # IIIF
        url = "/project/%s/tasks/import?type=iiif" % project.short_name
        res = self.app.get(url, follow_redirects=True)
        data = res.data.decode('utf-8')

        assert "From a IIIF manifest" in data
        assert 'action="/project/%E2%9C%93project1/tasks/import"' in data

        # Invalid
        url = "/project/%s/tasks/import?type=invalid" % project.short_name
        res = self.app.get(url, follow_redirects=True)

        assert res.status_code == 404, res.status_code

    @with_context
    @patch('pybossa.core.importer.get_all_importer_names')
    def test_get_importer_doesnt_show_unavailable_importers(self, names):
        names.return_value = ['csv', 'gdocs', 'epicollect', 's3']
        self.register()
        owner = db.session.query(User).first()
        project = ProjectFactory.create(owner=owner)
        url = "/project/%s/tasks/import" % project.short_name

        res = self.app.get(url, follow_redirects=True)

        assert "type=flickr"  not in str(res.data)
        assert "type=dropbox"  not in str(res.data)
        assert "type=twitter"  not in str(res.data)

    @with_context
    @patch('pybossa.view.projects.redirect_content_type', wraps=redirect)
    @patch('pybossa.importers.csv.requests.get')
    def test_import_tasks_redirects_on_success(self, request, redirect):
        """Test WEB when importing tasks succeeds, user is redirected to tasks main page"""
        csv_file = FakeResponse(text='Foo,Bar,Baz\n1,2,3', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        request.return_value = csv_file
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        url = '/project/%s/tasks/import' % project.short_name
        res = self.app.post(url, data={'csv_url': 'http://myfakecsvurl.com',
                                       'formtype': 'csv', 'form_name': 'csv'},
                            follow_redirects=True)

        assert "1 new task was imported successfully" in str(res.data)
        redirect.assert_called_with('/project/%s/tasks/' % project.short_name)

    @with_context
    @patch('pybossa.view.projects.importer.count_tasks_to_import')
    @patch('pybossa.view.projects.importer.create_tasks')
    def test_import_few_tasks_is_done_synchronously(self, create, count):
        """Test WEB importing a small amount of tasks is done synchronously"""
        count.return_value = 1
        create.return_value = ImportReport(message='1 new task was imported successfully', metadata=None, total=1)
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        url = '/project/%s/tasks/import' % project.short_name
        res = self.app.post(url, data={'csv_url': 'http://myfakecsvurl.com',
                                       'formtype': 'csv', 'form_name': 'csv'},
                            follow_redirects=True)

        assert "1 new task was imported successfully" in str(res.data)

    @with_context
    @patch('pybossa.view.projects.importer_queue', autospec=True)
    @patch('pybossa.view.projects.importer.count_tasks_to_import')
    def test_import_tasks_as_background_job(self, count_tasks, queue):
        """Test WEB importing a big amount of tasks is done in the background"""
        from pybossa.view.projects import MAX_NUM_SYNCHRONOUS_TASKS_IMPORT
        count_tasks.return_value = MAX_NUM_SYNCHRONOUS_TASKS_IMPORT + 1
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        url = '/project/%s/tasks/import' % project.short_name
        res = self.app.post(url, data={'csv_url': 'http://myfakecsvurl.com',
                                       'formtype': 'csv', 'form_name': 'csv'},
                            follow_redirects=True)
        tasks = db.session.query(Task).all()

        assert tasks == [], "Tasks should not be immediately added"
        data = {'type': 'csv', 'csv_url': 'http://myfakecsvurl.com'}
        queue.enqueue.assert_called_once_with(import_tasks, project.id, **data)
        msg = "You&#39;re trying to import a large amount of tasks, so please be patient.\
            You will receive an email when the tasks are ready."
        assert msg in str(res.data)

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    @patch('pybossa.importers.csv.requests.get')
    def test_bulk_csv_import_works(self, Mock, mock):
        """Test WEB bulk import works"""
        csv_file = FakeResponse(text='Foo,Bar,priority_0\n1,2,3', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        Mock.return_value = csv_file
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        url = '/project/%s/tasks/import' % (project.short_name)
        res = self.app.post(url, data={'csv_url': 'http://myfakecsvurl.com',
                                       'formtype': 'csv', 'form_name': 'csv'},
                            follow_redirects=True)
        task = db.session.query(Task).first()
        assert task is not None, task
        assert {'Bar': 2, 'Foo': 1} == task.info, task.info
        assert task.priority_0 == 3
        assert "1 new task was imported successfully" in str(res.data)

        # Check that only new items are imported
        empty_file = FakeResponse(text='Foo,Bar,priority_0\n1,2,3\n4,5,6',
                                  status_code=200,
                                  headers={'content-type': 'text/plain'},
                                  encoding='utf-8')
        Mock.return_value = empty_file
        project = db.session.query(Project).first()
        url = '/project/%s/tasks/import' % (project.short_name)
        res = self.app.post(url, data={'csv_url': 'http://myfakecsvurl.com',
                                       'formtype': 'csv', 'form_name': 'csv'},
                            follow_redirects=True)
        project = db.session.query(Project).first()
        err_msg = "There should be only 2 tasks"
        assert len(project.tasks) == 2, (err_msg, project.tasks)
        n = 0
        csv_tasks = [{'Foo': 1, 'Bar': 2}, {'Foo': 4, 'Bar': 5}]
        for t in project.tasks:
            assert t.info == csv_tasks[n], "The task info should be the same"
            n += 1

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    @patch('pybossa.importers.csv.requests.get')
    def test_bulk_gdocs_import_works(self, Mock, mock):
        """Test WEB bulk GDocs import works."""
        csv_file = FakeResponse(text='Foo,Bar,priority_0\n1,2,3', status_code=200,
                                headers={'content-type': 'text/plain'},
                                encoding='utf-8')
        Mock.return_value = csv_file
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        url = '/project/%s/tasks/import' % (project.short_name)
        res = self.app.post(url, data={'googledocs_url': 'http://drive.google.com',
                                       'formtype': 'gdocs', 'form_name': 'gdocs'},
                            follow_redirects=True)
        task = db.session.query(Task).first()
        assert {'Bar': 2, 'Foo': 1} == task.info
        assert task.priority_0 == 3
        assert "1 new task was imported successfully" in str(res.data)

        # Check that only new items are imported
        empty_file = FakeResponse(text='Foo,Bar,priority_0\n1,2,3\n4,5,6',
                                  status_code=200,
                                  headers={'content-type': 'text/plain'},
                                  encoding='utf-8')
        Mock.return_value = empty_file
        project = db.session.query(Project).first()
        url = '/project/%s/tasks/import' % (project.short_name)
        res = self.app.post(url, data={'googledocs_url': 'http://drive.google.com',
                                       'formtype': 'gdocs', 'form_name': 'gdocs'},
                            follow_redirects=True)
        project = db.session.query(Project).first()
        assert len(project.tasks) == 2, "There should be only 2 tasks"
        n = 0
        csv_tasks = [{'Foo': 1, 'Bar': 2}, {'Foo': 4, 'Bar': 5}]
        for t in project.tasks:
            assert t.info == csv_tasks[n], "The task info should be the same"
            n += 1

        # Check that only new items are imported
        project = db.session.query(Project).first()
        url = '/project/%s/tasks/import' % (project.short_name)
        res = self.app.post(url, data={'googledocs_url': 'http://drive.google.com',
                                       'formtype': 'gdocs', 'form_name': 'gdocs'},
                            follow_redirects=True)
        project = db.session.query(Project).first()
        assert len(project.tasks) == 2, "There should be only 2 tasks"
        n = 0
        csv_tasks = [{'Foo': 1, 'Bar': 2}, {'Foo': 4, 'Bar': 5}]
        for t in project.tasks:
            assert t.info == csv_tasks[n], "The task info should be the same"
            n += 1
        assert "no new records" in str(res.data), res.data

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    @patch('pybossa.importers.epicollect.requests.get')
    def test_bulk_epicollect_import_works(self, Mock, mock):
        """Test WEB bulk Epicollect import works"""
        data = [dict(DeviceID=23)]
        fake_response = FakeResponse(text=json.dumps(data), status_code=200,
                                     headers={'content-type': 'application/json'},
                                     encoding='utf-8')
        Mock.return_value = fake_response
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        res = self.app.post(('/project/%s/tasks/import' % (project.short_name)),
                            data={'epicollect_project': 'fakeproject',
                                  'epicollect_form': 'fakeform',
                                  'formtype': 'json', 'form_name': 'epicollect'},
                            follow_redirects=True)

        project = db.session.query(Project).first()
        err_msg = "Tasks should be imported"
        assert "1 new task was imported successfully" in str(res.data), err_msg
        tasks = db.session.query(Task).filter_by(project_id=project.id).all()
        err_msg = "The imported task from EpiCollect is wrong"
        assert tasks[0].info['DeviceID'] == 23, err_msg

        data = [dict(DeviceID=23), dict(DeviceID=24)]
        fake_response = FakeResponse(text=json.dumps(data), status_code=200,
                                     headers={'content-type': 'application/json'},
                                     encoding='utf-8')
        Mock.return_value = fake_response
        res = self.app.post(('/project/%s/tasks/import' % (project.short_name)),
                            data={'epicollect_project': 'fakeproject',
                                  'epicollect_form': 'fakeform',
                                  'formtype': 'json', 'form_name': 'epicollect'},
                            follow_redirects=True)
        project = db.session.query(Project).first()
        assert len(project.tasks) == 2, "There should be only 2 tasks"
        n = 0
        epi_tasks = [{'DeviceID': 23}, {'DeviceID': 24}]
        for t in project.tasks:
            assert t.info == epi_tasks[n], "The task info should be the same"
            n += 1

    @with_context
    @patch('pybossa.importers.flickr.requests.get')
    def test_bulk_flickr_import_works(self, request):
        """Test WEB bulk Flickr import works"""
        data = {
            "photoset": {
                "id": "72157633923521788",
                "primary": "8947113500",
                "owner": "32985084@N00",
                "ownername": "Teleyinex",
                "photo": [{"id": "8947115130", "secret": "00e2301a0d",
                           "server": "5441", "farm": 6, "title": "Title",
                           "isprimary": 0, "ispublic": 1, "isfriend": 0,
                           "isfamily": 0}
                          ],
                "page": 1,
                "per_page": "500",
                "perpage": "500",
                "pages": 1,
                "total": 1,
                "title": "Science Hack Day Balloon Mapping Workshop"},
            "stat": "ok"}
        fake_response = FakeResponse(text=json.dumps(data), status_code=200,
                                     headers={'content-type': 'application/json'},
                                     encoding='utf-8')
        request.return_value = fake_response
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        res = self.app.post(('/project/%s/tasks/import' % (project.short_name)),
                            data={'album_id': '1234',
                                  'form_name': 'flickr'},
                            follow_redirects=True)

        project = db.session.query(Project).first()
        err_msg = "Tasks should be imported"
        assert "1 new task was imported successfully" in str(res.data), err_msg
        tasks = db.session.query(Task).filter_by(project_id=project.id).all()
        expected_info = {
            'url': 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d.jpg',
            'url_m': 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d_m.jpg',
            'url_b': 'https://farm6.staticflickr.com/5441/8947115130_00e2301a0d_b.jpg',
            'link': 'https://www.flickr.com/photos/32985084@N00/8947115130',
            'title': 'Title'}
        assert tasks[0].info == expected_info, tasks[0].info

    @with_context
    def test_flickr_importer_page_shows_option_to_log_into_flickr(self):
        self.register()
        owner = db.session.query(User).first()
        project = ProjectFactory.create(owner=owner)
        url = "/project/%s/tasks/import?type=flickr" % project.short_name

        res = self.app.get(url)
        login_url = '/flickr/?next=%2Fproject%2F%25E2%259C%2593project1%2Ftasks%2Fimport%3Ftype%3Dflickr'

        assert login_url in str(res.data)

    @with_context
    def test_bulk_dropbox_import_works(self):
        """Test WEB bulk Dropbox import works"""
        dropbox_file_data = ('{"bytes":286,'
                             '"link":"https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?dl=0",'
                             '"name":"test.txt",'
                             '"icon":"https://www.dropbox.com/static/images/icons64/page_white_text.png"}')
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        res = self.app.post('/project/%s/tasks/import' % project.short_name,
                            data={'files-0': dropbox_file_data,
                                  'form_name': 'dropbox'},
                            follow_redirects=True)

        project = db.session.query(Project).first()
        err_msg = "Tasks should be imported"
        tasks = db.session.query(Task).filter_by(project_id=project.id).all()
        expected_info = {
            'link_raw': 'https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?raw=1',
            'link': 'https://www.dropbox.com/s/l2b77qvlrequ6gl/test.txt?dl=0',
            'filename': 'test.txt'}
        assert tasks[0].info == expected_info, tasks[0].info

    @with_context
    @patch('pybossa.importers.twitterapi.Twitter')
    @patch('pybossa.importers.twitterapi.oauth2_dance')
    def test_bulk_twitter_import_works(self, oauth, client):
        """Test WEB bulk Twitter import works"""
        tweet_data = {
            'statuses': [
                {
                    'created_at': 'created',
                    'favorite_count': 77,
                    'coordinates': 'coords',
                    'id_str': '1',
                    'id': 1,
                    'retweet_count': 44,
                    'user': {'screen_name': 'fulanito'},
                    'text': 'this is a tweet #match'
                }
            ]
        }
        client_instance = Mock()
        client_instance.search.tweets.return_value = tweet_data
        client.return_value = client_instance

        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        res = self.app.post('/project/%s/tasks/import' % project.short_name,
                            data={'source': '#match',
                                  'max_tweets': 1,
                                  'form_name': 'twitter'},
                            follow_redirects=True)

        project = db.session.query(Project).first()
        err_msg = "Tasks should be imported"
        tasks = db.session.query(Task).filter_by(project_id=project.id).all()
        expected_info = {
            'created_at': 'created',
            'favorite_count': 77,
            'coordinates': 'coords',
            'id_str': '1',
            'id': 1,
            'retweet_count': 44,
            'user': {'screen_name': 'fulanito'},
            'user_screen_name': 'fulanito',
            'text': 'this is a tweet #match'
        }
        assert tasks[0].info == expected_info, tasks[0].info

    @with_context
    def test_bulk_s3_import_works(self):
        """Test WEB bulk S3 import works"""
        self.register()
        self.new_project()
        project = db.session.query(Project).first()
        res = self.app.post('/project/%s/tasks/import' % project.short_name,
                            data={'files-0': 'myfile.txt',
                                  'bucket': 'mybucket',
                                  'form_name': 's3'},
                            follow_redirects=True)

        project = db.session.query(Project).first()
        err_msg = "Tasks should be imported"
        tasks = db.session.query(Task).filter_by(project_id=project.id).all()
        expected_info = {
            'url': 'https://mybucket.s3.amazonaws.com/myfile.txt',
            'filename': 'myfile.txt',
            'link': 'https://mybucket.s3.amazonaws.com/myfile.txt'
        }
        assert tasks[0].info == expected_info, tasks[0].info

    @with_context
    def test_55_facebook_account_warning(self):
        """Test WEB Facebook OAuth user gets a hint to sign in"""
        user = User(fullname='John',
                    name='john',
                    email_addr='john@john.com',
                    info={})

        user.info = dict(facebook_token='facebook')
        msg, method = get_user_signup_method(user)
        err_msg = "Should return 'facebook' but returned %s" % method
        assert method == 'facebook', err_msg

        user.info = dict(google_token='google')
        msg, method = get_user_signup_method(user)
        err_msg = "Should return 'google' but returned %s" % method
        assert method == 'google', err_msg

        user.info = dict(twitter_token='twitter')
        msg, method = get_user_signup_method(user)
        err_msg = "Should return 'twitter' but returned %s" % method
        assert method == 'twitter', err_msg

        user.info = {}
        msg, method = get_user_signup_method(user)
        err_msg = "Should return 'local' but returned %s" % method
        assert method == 'local', err_msg

    @with_context
    def test_56_delete_tasks(self):
        """Test WEB delete tasks works"""
        Fixtures.create()
        # Anonymous user
        res = self.app.get('/project/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Anonymous user should be redirected for authentication"
        assert "Please sign in to access this page" in str(res.data), err_msg
        err_msg = "Anonymous user should not be allowed to delete tasks"
        res = self.app.post('/project/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Anonymous user should not be allowed to delete tasks"
        assert "Please sign in to access this page" in str(res.data), err_msg

        # Authenticated user but not owner
        self.register()
        res = self.app.get('/project/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Authenticated user but not owner should get 403 FORBIDDEN in GET"
        assert res.status == '403 FORBIDDEN', err_msg
        res = self.app.post('/project/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Authenticated user but not owner should get 403 FORBIDDEN in POST"
        assert res.status == '403 FORBIDDEN', err_msg
        self.signout()

        # Owner
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        res = self.signin(email='tester@tester.com', password='tester')
        res = self.app.get('/project/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Owner user should get 200 in GET"
        assert res.status == '200 OK', err_msg
        assert len(tasks) > 0, "len(project.tasks) > 0"
        res = self.app.post('/project/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Owner should get 200 in POST"
        assert res.status == '200 OK', err_msg
        tasks = db.session.query(Task).filter_by(project_id=1).all()
        assert len(tasks) == 0, "len(project.tasks) != 0"

        # Admin
        res = self.signin(email='root@root.com', password='tester' + 'root')
        res = self.app.get('/project/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Admin user should get 200 in GET"
        assert res.status_code == 200, err_msg
        res = self.app.post('/project/test-app/tasks/delete', follow_redirects=True)
        err_msg = "Admin should get 200 in POST"
        assert res.status_code == 200, err_msg

    @with_context
    def test_56_delete_tasks_json(self):
        """Test WEB delete tasks JSON works"""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        TaskFactory.create(project=project)
        url = '/project/%s/tasks/delete' % project.short_name

        # Anonymous user
        res = self.app_get_json(url, follow_redirects=True)
        err_msg = "Anonymous user should be redirected for authentication"
        assert "Please sign in to access this page" in str(res.data), err_msg
        err_msg = "Anonymous user should not be allowed to delete tasks"
        res = self.app.post(url, follow_redirects=True)
        err_msg = "Anonymous user should not be allowed to delete tasks"
        assert "Please sign in to access this page" in str(res.data), err_msg

        # Authenticated user but not owner
        res = self.app_get_json(url + '?api_key=%s' % user.api_key)
        err_msg = "Authenticated user but not owner should get 403 FORBIDDEN in GET"
        assert res.status == '403 FORBIDDEN', err_msg
        res = self.app.post(url + '?api_key=%s' % user.api_key)
        err_msg = "Authenticated user but not owner should get 403 FORBIDDEN in POST"
        assert res.status == '403 FORBIDDEN', err_msg

        # Owner
        tasks = db.session.query(Task).filter_by(project_id=project.id).all()
        res = self.app_get_json(url + '?api_key=%s' % owner.api_key)
        err_msg = "Owner user should get 200 in GET"
        assert res.status == '200 OK', err_msg
        assert len(tasks) > 0, "len(project.tasks) > 0"
        res = self.app_post_json(url + '?api_key=%s' % owner.api_key)
        err_msg = "Owner should get 200 in POST"
        assert res.status == '200 OK', err_msg
        tasks = db.session.query(Task).filter_by(project_id=project.id).all()
        assert len(tasks) == 0, "len(project.tasks) != 0"

        # Admin
        res = self.app.get(url + '?api_key=%s' % admin.api_key)
        err_msg = "Admin user should get 200 in GET"
        assert res.status_code == 200, err_msg
        res = self.app_post_json(url + '?api_key=%s' % admin.api_key)
        err_msg = "Admin should get 200 in POST"
        assert res.status_code == 200, err_msg


    @with_context
    @patch('pybossa.repositories.task_repository.uploader')
    def test_delete_tasks_removes_existing_zip_files(self, uploader):
        """Test WEB delete tasks also deletes zip files for task and taskruns"""
        Fixtures.create()
        self.signin(email='tester@tester.com', password='tester')
        res = self.app.post('/project/test-app/tasks/delete', follow_redirects=True)
        expected = [call('1_test-app_task_json.zip', 'user_2'),
                    call('1_test-app_task_csv.zip', 'user_2'),
                    call('1_test-app_task_run_json.zip', 'user_2'),
                    call('1_test-app_task_run_csv.zip', 'user_2')]
        assert uploader.delete_file.call_args_list == expected

    @with_context
    def test_57_reset_api_key(self):
        """Test WEB reset api key works"""
        url = "/account/johndoe/update"
        # Anonymous user
        res = self.app.get(url, follow_redirects=True)
        err_msg = "Anonymous user should be redirected for authentication"
        assert "Please sign in to access this page" in str(res.data), err_msg
        res = self.app.post(url, follow_redirects=True)
        assert "Please sign in to access this page" in str(res.data), err_msg
        # Authenticated user
        self.register()
        user = db.session.query(User).get(1)
        url = "/account/%s/update" % user.name
        api_key = user.api_key
        res = self.app.get(url, follow_redirects=True)
        err_msg = "Authenticated user should get access to reset api key page"
        assert res.status_code == 200, err_msg
        assert "reset your personal API Key" in str(res.data), err_msg
        url = "/account/%s/resetapikey" % user.name
        res = self.app.post(url, follow_redirects=True)
        err_msg = "Authenticated user should be able to reset his api key"
        assert res.status_code == 200, err_msg
        user = db.session.query(User).get(1)
        err_msg = "New generated API key should be different from old one"
        assert api_key != user.api_key, err_msg
        self.signout()

        self.register(fullname="new", name="new")
        res = self.app.post(url)
        assert res.status_code == 403, res.status_code

        url = "/account/fake/resetapikey"
        res = self.app.post(url)
        assert res.status_code == 404, res.status_code

    @with_context
    def test_57_reset_api_key_json(self):
        """Test WEB reset api key JSON works"""
        url = "/account/johndoe/update"
        # Anonymous user
        res = self.app_get_json(url, follow_redirects=True)
        err_msg = "Anonymous user should be redirected for authentication"
        assert "Please sign in to access this page" in str(res.data), err_msg
        res = self.app_post_json(url, data=dict(foo=1), follow_redirects=True)
        assert "Please sign in to access this page" in str(res.data), res.data
        # Authenticated user
        self.register()
        user = db.session.query(User).get(1)
        url = "/account/%s/update" % user.name
        api_key = user.api_key
        res = self.app_get_json(url, follow_redirects=True)
        err_msg = "Authenticated user should get access to reset api key page"
        assert res.status_code == 200, err_msg
        data = json.loads(res.data)
        assert data.get('form').get('name') == user.name, (err_msg, data)

        with patch.dict(self.flask_app.config, {'WTF_CSRF_ENABLED': True}):
            url = "/account/%s/resetapikey" % user.name
            csrf = self.get_csrf(url)
            headers = {'X-CSRFToken': csrf}
            res = self.app_post_json(url,
                                     follow_redirects=True, headers=headers)
            err_msg = "Authenticated user should be able to reset his api key"
            assert res.status_code == 200, err_msg
            data = json.loads(res.data)
            assert data.get('status') == SUCCESS, err_msg
            assert data.get('next') == "/account/%s/" % user.name, (err_msg, data)
            user = db.session.query(User).get(1)
            err_msg = "New generated API key should be different from old one"
            assert api_key != user.api_key, (err_msg, data)
            self.signout()

            self.register(fullname="new", name="new")
            res = self.app_post_json(url, headers=headers)
            assert res.status_code == 403, res.status_code
            data = json.loads(res.data)
            assert data.get('code') == 403, data

            url = "/account/fake/resetapikey"
            res = self.app_post_json(url, headers=headers)
            assert res.status_code == 404, res.status_code
            data = json.loads(res.data)
            assert data.get('code') == 404, data


    @with_context
    def test_58_global_stats(self):
        """Test WEB global stats of the site works"""
        Fixtures.create()

        url = "/stats"
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be a Global Statistics page of the project"
        assert "General Statistics" in str(res.data), err_msg

    @with_context
    def test_58_global_stats_json(self):
        """Test WEB global stats JSON of the site works"""
        Fixtures.create()

        url = "/stats/"
        res = self.app_get_json(url)
        err_msg = "There should be a Global Statistics page of the project"
        data = json.loads(res.data)
        keys = ['projects', 'show_locs', 'stats', 'tasks', 'top5_projects_24_hours', 'top5_users_24_hours', 'users']
        assert keys.sort() == list(data.keys()).sort(), keys


    @with_context
    def test_59_help_api(self):
        """Test WEB help api page exists"""
        Fixtures.create()
        url = "/help/api"
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be a help api page"
        assert "API Help" in str(res.data), err_msg
        assert_raises(ValueError, json.loads, res.data)

    @with_context
    def test_59_help_api_json(self):
        """Test WEB help api json exists"""
        Fixtures.create()
        url = "/help/api"
        res = self.app_get_json(url, follow_redirects=True)
        data = json.loads(res.data)
        err_msg = 'Template wrong'
        assert data['template'] == 'help/api.html', err_msg
        err_msg = 'Title wrong'
        assert data['title'] == 'Help: API', err_msg
        err_msg = 'project id missing'
        assert 'project_id' in str(data), err_msg

    @with_context
    def test_59_help_license(self):
        """Test WEB help license page exists."""
        url = "/help/license"
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be a help license page"
        assert "Licenses" in str(res.data), err_msg
        assert_raises(ValueError, json.loads, res.data)

    @with_context
    def test_59_help_license_json(self):
        """Test WEB help license json exists."""
        url = "/help/license"
        res = self.app_get_json(url, follow_redirects=True)
        data = json.loads(res.data)
        err_msg = 'Template wrong'
        assert data['template'] == 'help/license.html', err_msg
        err_msg = 'Title wrong'
        assert data['title'] == 'Help: Licenses', err_msg

    @with_context
    def test_59_about(self):
        """Test WEB help about page exists."""
        url = "/about"
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be an about page"
        assert "About" in str(res.data), err_msg

    @with_context
    def test_59_help_tos(self):
        """Test WEB help TOS page exists."""
        url = "/help/terms-of-use"
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be a TOS page"
        assert "Terms for use" in str(res.data), err_msg
        assert_raises(ValueError, json.loads, res.data)

    @with_context
    def test_59_help_tos_json(self):
        """Test WEB help TOS json endpoint exists"""
        url = "/help/terms-of-use"
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = 'Template wrong'
        assert data['template'] == 'help/tos.html', err_msg
        err_msg = 'Title wrong'
        assert data['title'] == 'Help: Terms of Use', err_msg
        err_msg = "There should be HTML content"
        assert '<body' in data['content'], err_msg

    @with_context
    def test_59_help_cookies_policy(self):
        """Test WEB help cookies policy page exists."""
        url = "/help/cookies-policy"
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be a TOS page"
        assert "uses cookies" in str(res.data), err_msg
        assert_raises(ValueError, json.loads, res.data)

    @with_context
    def test_59_help_cookies_policy_json(self):
        """Test WEB help cookies policy json endpoint exists."""
        url = "/help/cookies-policy"
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = 'Template wrong'
        assert data['template'] == 'help/cookies_policy.html', err_msg
        err_msg = 'Title wrong'
        assert data['title'] == 'Help: Cookies Policy', err_msg
        err_msg = "There should be HTML content"
        assert '<body' in data['content'], err_msg

    @with_context
    def test_59_help_privacy(self):
        """Test WEB help privacy page exists."""
        url = "/help/privacy"
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be a privacy policy page"
        assert "Privacy" in str(res.data), err_msg
        assert_raises(ValueError, json.loads, res.data)

    @with_context
    def test_60_help_privacy_json(self):
        """Test privacy json endpoint"""
        url = "/help/privacy"
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg = 'Template wrong'
        assert data['template'] == 'help/privacy.html', err_msg
        err_msg = 'Title wrong'
        assert data['title'] == 'Privacy Policy', err_msg
        err_msg = "There should be HTML content"
        assert '<body' in data['content'], err_msg

    @with_context
    def test_69_allow_anonymous_contributors(self):
        """Test WEB allow anonymous contributors works"""
        Fixtures.create()
        project = db.session.query(Project).first()
        url = '/project/%s/newtask' % project.short_name

        # All users are allowed to participate by default
        # As Anonymous user
        res = self.app.get(url, follow_redirects=True)
        err_msg = "The anonymous user should be able to participate"
        assert project.name in str(res.data), err_msg

        # As registered user
        self.register()
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        err_msg = "The anonymous user should be able to participate"
        assert project.name in str(res.data), err_msg
        self.signout()

        # Now only allow authenticated users
        project.allow_anonymous_contributors = False
        db.session.add(project)
        db.session.commit()

        # As Anonymous user
        res = self.app.get(url, follow_redirects=True)
        err_msg = "User should be redirected to sign in"
        project = db.session.query(Project).first()
        msg = "Oops! You have to sign in to participate in <strong>%s</strong>" % project.name
        assert msg in str(res.data), err_msg

        # As registered user
        res = self.signin()
        res = self.app.get(url, follow_redirects=True)
        err_msg = "The authenticated user should be able to participate"
        assert project.name in str(res.data), err_msg
        self.signout()

        # Now only allow authenticated users
        project.allow_anonymous_contributors = False
        db.session.add(project)
        db.session.commit()
        res = self.app.get(url, follow_redirects=True)
        err_msg = "Only authenticated users can participate"
        assert "You have to sign in" in str(res.data), err_msg

    @with_context
    def test_70_public_user_profile(self):
        """Test WEB public user profile works"""
        Fixtures.create()

        # Should work as an anonymous user
        url = '/account/%s/' % Fixtures.name
        res = self.app.get(url, follow_redirects=True)
        err_msg = "There should be a public profile page for the user"
        assert Fixtures.fullname in str(res.data), err_msg

        # Should work as an authenticated user
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        assert Fixtures.fullname in str(res.data), err_msg

        # Should return 404 when a user does not exist
        url = '/account/a-fake-name-that-does-not-exist/'
        res = self.app.get(url, follow_redirects=True)
        err_msg = "It should return a 404"
        assert res.status_code == 404, err_msg

    @with_context
    def test_71_public_user_profile_json(self):
        """Test JSON WEB public user profile works"""

        res = self.app.get('/account/nonexistent/',
                           content_type='application/json')
        assert res.status_code == 404, res.status_code
        data = json.loads(res.data)
        assert data['code'] == 404, res.status_code

        Fixtures.create()

        # Should work as an anonymous user
        url = '/account/%s/' % Fixtures.name
        res = self.app.get(url, content_type='application/json')
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        err_msg = 'there should be a title for the user page'
        assert data['title'] == 'T Tester &middot; User Profile', err_msg
        err_msg = 'there should be a user name'
        assert data['user']['name'] == 'tester', err_msg
        err_msg = 'there should not be a user id'
        assert 'id' not in data['user'], err_msg

    @with_context
    def test_72_profile_url_json(self):
        """Test JSON WEB public user profile works"""

        res = self.app.get('/account/profile',
                           content_type='application/json')
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert data['next'] == '/account/signin'
        assert data['status'] == 'not_signed_in'

    @with_context
    def test_72_profile_url_json_restrict(self):
        """Test JSON WEB public user profile restrict works"""

        user = UserFactory.create(restrict=True)
        admin = UserFactory.create(admin=True)
        other = UserFactory.create()

        url = '/account/profile?api_key=%s' % user.api_key

        res = self.app.get(url,
                           content_type='application/json')
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert data.get('user') is not None, data
        userDict = data.get('user')
        assert userDict['id'] == user.id, userDict
        assert userDict['restrict'] is True, userDict

        # As admin should return nothing
        url = '/account/%s/?api_key=%s' % (user.name, admin.api_key)

        res = self.app.get(url,
                           content_type='application/json')
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert data.get('user') is None, data
        assert data.get('title') == 'User data is restricted'
        assert data.get('can_update') is False
        assert data.get('projects_created') == []
        assert data.get('projects') == [], data

        # As another user should return nothing
        url = '/account/%s/?api_key=%s' % (user.name, other.api_key)

        res = self.app.get(url,
                           content_type='application/json')
        assert res.status_code == 200, res.status_code
        data = json.loads(res.data)
        assert data.get('user') is None, data
        assert data.get('title') == 'User data is restricted'
        assert data.get('can_update') is False
        assert data.get('projects_created') == []
        assert data.get('projects') == [], data



    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_74_task_settings_page(self, mock):
        """Test WEB TASK SETTINGS page works"""
        # Creat root user
        self.register()
        self.signout()
        # As owner
        self.register(fullname="owner", name="owner")
        res = self.new_project()
        url = "/project/sampleapp/tasks/settings"

        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        divs = ['task_scheduler', 'task_delete', 'task_redundancy']
        for div in divs:
            err_msg = "There should be a %s section" % div
            assert dom.find(id=div) is not None, err_msg

        self.signout()
        # As an authenticated user
        self.register(fullname="juan", name="juan")
        res = self.app.get(url, follow_redirects=True)
        err_msg = "User should not be allowed to access this page"
        assert res.status_code == 403, err_msg
        self.signout()

        # As an anonymous user
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "User should be redirected to sign in"
        assert dom.find(id="signin") is not None, err_msg

        # As root
        self.signin()
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        divs = ['task_scheduler', 'task_delete', 'task_redundancy']
        for div in divs:
            err_msg = "There should be a %s section" % div
            assert dom.find(id=div) is not None, err_msg

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_75_task_settings_scheduler(self, mock):
        """Test WEB TASK SETTINGS scheduler page works"""
        # Creat root user
        self.register()
        self.signout()
        # Create owner
        self.register(fullname="owner", name="owner")
        self.new_project()
        url = "/project/sampleapp/tasks/scheduler"
        form_id = 'task_scheduler'
        self.signout()

        # As owner and root
        for i in range(0, 1):
            if i == 0:
                # As owner
                self.signin(email="owner@example.com")
                sched = 'depth_first'
            else:
                sched = 'default'
                self.signin()
            res = self.app.get(url, follow_redirects=True)
            dom = BeautifulSoup(res.data)
            err_msg = "There should be a %s section" % form_id
            assert dom.find(id=form_id) is not None, err_msg
            res = self.task_settings_scheduler(short_name="sampleapp",
                                               sched=sched)
            err_msg = "Task Scheduler should be updated"
            assert "Project Task Scheduler updated" in str(res.data), err_msg
            assert "success" in str(res.data), err_msg
            project = db.session.query(Project).get(1)
            assert project.info['sched'] == sched, err_msg
            self.signout()

        # As an authenticated user
        self.register(fullname="juan", name="juan")
        res = self.app.get(url, follow_redirects=True)
        err_msg = "User should not be allowed to access this page"
        assert res.status_code == 403, err_msg
        self.signout()

        # As an anonymous user
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "User should be redirected to sign in"
        assert dom.find(id="signin") is not None, err_msg


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_75_task_settings_scheduler_json(self, mock):
        """Test WEB TASK SETTINGS JSON scheduler page works"""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        url = "/project/%s/tasks/scheduler" % project.short_name
        form_id = 'task_scheduler'

        # As owner and root
        for i in range(0, 1):
            if i == 0:
                # As owner
                new_url = url + '?api_key=%s' % owner.api_key
                sched = 'depth_first'
            else:
                new_url = url + '?api_key=%s' % admin.api_key
                sched = 'default'
            res = self.app_get_json(new_url)
            data = json.loads(res.data)
            assert data['form']['csrf'] is not None, data
            assert 'sched' in list(data['form'].keys()), data

            res = self.app_post_json(new_url, data=dict(sched=sched))
            data = json.loads(res.data)
            project = db.session.query(Project).get(1)
            assert project.info['sched'] == sched, err_msg
            assert data['status'] == SUCCESS, data

        # As an authenticated user
        res = self.app_get_json(url + '?api_key=%s' % user.api_key)
        err_msg = "User should not be allowed to access this page"
        assert res.status_code == 403, err_msg

        # As an anonymous user
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "User should be redirected to sign in"
        assert dom.find(id="signin") is not None, err_msg


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_76_task_settings_redundancy(self, mock):
        """Test WEB TASK SETTINGS redundancy page works"""
        # Creat root user
        self.register()
        self.signout()
        # Create owner
        self.register(fullname="owner", name="owner")
        self.new_project()
        self.new_task(1)

        url = "/project/sampleapp/tasks/redundancy"
        form_id = 'task_redundancy'
        self.signout()

        # As owner and root
        for i in range(0, 1):
            if i == 0:
                # As owner
                self.signin(email="owner@example.com")
                n_answers = 20
            else:
                n_answers = 10
                self.signin()
            res = self.app.get(url, follow_redirects=True)
            dom = BeautifulSoup(res.data)
            # Correct values
            err_msg = "There should be a %s section" % form_id
            assert dom.find(id=form_id) is not None, err_msg
            res = self.task_settings_redundancy(short_name="sampleapp",
                                                n_answers=n_answers)
            db.session.close()
            err_msg = "Task Redundancy should be updated"
            assert "Redundancy of Tasks updated" in str(res.data), err_msg
            assert "success" in str(res.data), err_msg
            project = db.session.query(Project).get(1)
            for t in project.tasks:
                assert t.n_answers == n_answers, err_msg
            # Wrong values, triggering the validators
            res = self.task_settings_redundancy(short_name="sampleapp",
                                                n_answers=0)
            err_msg = "Task Redundancy should be a value between 0 and 1000"
            assert "error" in str(res.data), err_msg
            assert "success" not in str(res.data), err_msg
            res = self.task_settings_redundancy(short_name="sampleapp",
                                                n_answers=10000000)
            err_msg = "Task Redundancy should be a value between 0 and 1000"
            assert "error" in str(res.data), err_msg
            assert "success" not in str(res.data), err_msg

            self.signout()

        # As an authenticated user
        self.register(fullname="juan", name="juan")
        res = self.app.get(url, follow_redirects=True)
        err_msg = "User should not be allowed to access this page"
        assert res.status_code == 403, err_msg
        self.signout()

        # As an anonymous user
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "User should be redirected to sign in"
        assert dom.find(id="signin") is not None, err_msg


    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_76_task_settings_redundancy_json(self, mock):
        """Test WEB TASK SETTINGS redundancy JSON page works"""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)

        url = "/project/%s/tasks/redundancy" % project.short_name
        form_id = 'task_redundancy'

        # As owner and root
        for i in range(0, 1):
            if i == 0:
                # As owner
                new_url = url + '?api_key=%s' % owner.api_key
                self.signin(email="owner@example.com")
                n_answers = 20
            else:
                new_url = url + '?api_key=%s' % admin.api_key
                n_answers = 10
                self.signin()
            res = self.app_get_json(new_url)
            data = json.loads(res.data)
            assert data['form']['csrf'] is not None, data
            assert 'n_answers' in list(data['form'].keys()), data

            res = self.app_post_json(new_url, data=dict(n_answers=n_answers))
            data = json.loads(res.data)
            assert data['status'] == SUCCESS, data
            project = db.session.query(Project).get(1)
            for t in project.tasks:
                assert t.n_answers == n_answers, err_msg

            res = self.app_post_json(new_url, data=dict(n_answers=-1))
            data = json.loads(res.data)
            err_msg = "Task Redundancy should be a value between 1 and 1000"
            assert data['status'] == 'error', data
            assert 'between 1 and 1,000' in data['form']['errors']['n_answers'][0], data

            res = self.app_post_json(new_url, data=dict(n_answers=10000000000))
            data = json.loads(res.data)
            err_msg = "Task Redundancy should be a value between 1 and 1000"
            assert data['status'] == 'error', data
            assert 'between 1 and 1,000' in data['form']['errors']['n_answers'][0], err_msg

        # As an authenticated user
        res = self.app_get_json(url + '?api_key=%s' % user.api_key)
        err_msg = "User should not be allowed to access this page"
        assert res.status_code == 403, err_msg

        # As an anonymous user
        res = self.app_get_json(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "User should be redirected to sign in"
        assert dom.find(id="signin") is not None, err_msg


    @with_context
    def test_task_redundancy_update_updates_task_state(self):
        """Test WEB when updating the redundancy of the tasks in a project, the
        state of the task is updated in consecuence"""
        # Creat root user
        self.register()
        self.new_project()
        self.new_task(1)

        url = "/project/sampleapp/tasks/redundancy"

        project = db.session.query(Project).get(1)
        for t in project.tasks:
            tr = TaskRun(project_id=project.id, task_id=t.id)
            db.session.add(tr)
            db.session.commit()

        err_msg = "Task state should be completed"
        res = self.task_settings_redundancy(short_name="sampleapp",
                                            n_answers=1)

        for t in project.tasks:
            assert t.state == 'completed', err_msg

        res = self.task_settings_redundancy(short_name="sampleapp",
                                            n_answers=2)
        err_msg = "Task state should be ongoing"
        db.session.add(project)
        db.session.commit()

        for t in project.tasks:
            assert t.state == 'ongoing', t.state

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_77_task_settings_priority(self, mock):
        """Test WEB TASK SETTINGS priority page works"""
        # Creat root user
        self.register()
        self.signout()
        # Create owner
        self.register(fullname="owner", name="owner")
        self.new_project()
        self.new_task(1)
        url = "/project/sampleapp/tasks/priority"
        form_id = 'task_priority'
        self.signout()

        # As owner and root
        project = db.session.query(Project).get(1)
        _id = project.tasks[0].id
        for i in range(0, 1):
            if i == 0:
                # As owner
                self.signin(email="owner@example.com")
                task_ids = str(_id)
                priority_0 = 1.0
            else:
                task_ids = "1"
                priority_0 = 0.5
                self.signin()
            res = self.app.get(url, follow_redirects=True)
            dom = BeautifulSoup(res.data)
            # Correct values
            err_msg = "There should be a %s section" % form_id
            assert dom.find(id=form_id) is not None, err_msg
            res = self.task_settings_priority(short_name="sampleapp",
                                              task_ids=task_ids,
                                              priority_0=priority_0)
            err_msg = "Task Priority should be updated"
            assert "error" not in str(res.data), err_msg
            assert "success" in str(res.data), err_msg
            task = db.session.query(Task).get(_id)
            assert task.id == int(task_ids), err_msg
            assert task.priority_0 == priority_0, err_msg
            # Wrong values, triggering the validators
            res = self.task_settings_priority(short_name="sampleapp",
                                              priority_0=3,
                                              task_ids="1")
            err_msg = "Task Priority should be a value between 0.0 and 1.0"
            assert "error" in str(res.data), err_msg
            assert "success" not in str(res.data), err_msg
            res = self.task_settings_priority(short_name="sampleapp",
                                              task_ids="1, 2")
            err_msg = "Task Priority task_ids should be a comma separated, no spaces, integers"
            assert "error" in str(res.data), err_msg
            assert "success" not in str(res.data), err_msg
            res = self.task_settings_priority(short_name="sampleapp",
                                              task_ids="1,a")
            err_msg = "Task Priority task_ids should be a comma separated, no spaces, integers"
            assert "error" in str(res.data), err_msg
            assert "success" not in str(res.data), err_msg

            self.signout()

        # As an authenticated user
        self.register(fullname="juan", name="juan")
        res = self.app.get(url, follow_redirects=True)
        err_msg = "User should not be allowed to access this page"
        assert res.status_code == 403, err_msg
        self.signout()

        # As an anonymous user
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "User should be redirected to sign in"
        assert dom.find(id="signin") is not None, err_msg

    @with_context
    @patch('pybossa.view.projects.uploader.upload_file', return_value=True)
    def test_77_task_settings_priority_json(self, mock):
        """Test WEB TASK SETTINGS JSON priority page works"""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(owner=owner)
        TaskFactory.create(project=project)
        url = "/project/%s/tasks/priority" % project.short_name
        form_id = 'task_priority'

        # As owner and root
        project = db.session.query(Project).get(project.id)
        _id = project.tasks[0].id
        for i in range(0, 1):
            if i == 0:
                # As owner
                new_url = url + '?api_key=%s' % owner.api_key
                task_ids = str(_id)
                priority_0 = 1.0
            else:
                new_url = url + '?api_key=%s' % admin.api_key
                task_ids = "1"
                priority_0 = 0.5
            res = self.app_get_json(new_url)
            data = json.loads(res.data)
            assert data['form']['csrf'] is not None, data
            assert 'priority_0' in list(data['form'].keys()), data
            assert 'task_ids' in list(data['form'].keys()), data
            res = self.app_post_json(new_url, data=dict(task_ids=task_ids,
                                                        priority_0=priority_0))
            data = json.loads(res.data)
            assert data['status'] == SUCCESS, data

            err_msg = "Priority should be changed."
            task = db.session.query(Task).get(_id)
            assert task.id == int(task_ids), err_msg
            assert task.priority_0 == priority_0, err_msg
            # Wrong values, triggering the validators
            res = self.app_post_json(new_url, data=dict(priority_0=3, task_ids="1"))
            data = json.loads(res.data)
            assert data['status'] == 'error', data
            assert len(data['form']['errors']['priority_0']) == 1, data


            res = self.app_post_json(new_url, data=dict(priority_0=3, task_ids="1, 2"))
            data = json.loads(res.data)
            assert data['status'] == 'error', data
            assert len(data['form']['errors']['task_ids']) == 1, data

            res = self.app_post_json(new_url, data=dict(priority_0=3, task_ids="1, a"))
            data = json.loads(res.data)
            assert data['status'] == 'error', data
            assert len(data['form']['errors']['task_ids']) == 1, data


        # As an authenticated user
        res = self.app.get(url + '?api_key=%s' % user.api_key)
        err_msg = "User should not be allowed to access this page"
        assert res.status_code == 403, err_msg

        # As an anonymous user
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "User should be redirected to sign in"
        assert dom.find(id="signin") is not None, err_msg


    @with_context
    def test_78_cookies_warning(self):
        """Test WEB cookies warning is displayed"""
        # As Anonymous
        res = self.app.get('/', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "If cookies are not accepted, cookies banner should be shown"
        assert dom.find(id='cookies_warning') is not None, err_msg

        # As user
        self.signin(email=Fixtures.email_addr2, password=Fixtures.password)
        res = self.app.get('/', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "If cookies are not accepted, cookies banner should be shown"
        assert dom.find(id='cookies_warning') is not None, err_msg
        self.signout()

        # As admin
        self.signin(email=Fixtures.root_addr, password=Fixtures.root_password)
        res = self.app.get('/', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "If cookies are not accepted, cookies banner should be shown"
        assert dom.find(id='cookies_warning') is not None, err_msg
        self.signout()

    @with_context
    def test_79_cookies_warning2(self):
        """Test WEB cookies warning is hidden"""
        # As Anonymous
        self.app.set_cookie("localhost", "cookieconsent_dismissed", "Yes")
        res = self.app.get('/', follow_redirects=True, headers={})
        dom = BeautifulSoup(res.data)
        err_msg = "If cookies are not accepted, cookies banner should be hidden"
        assert dom.find('div', attrs={'class': 'cc_banner-wrapper'}) is None, err_msg

        # As user
        self.signin(email=Fixtures.email_addr2, password=Fixtures.password)
        res = self.app.get('/', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "If cookies are not accepted, cookies banner should be hidden"
        assert dom.find('div', attrs={'class': 'cc_banner-wrapper'}) is None, err_msg
        self.signout()

        # As admin
        self.signin(email=Fixtures.root_addr, password=Fixtures.root_password)
        res = self.app.get('/', follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "If cookies are not accepted, cookies banner should be hidden"
        assert dom.find('div', attrs={'class': 'cc_banner-wrapper'}) is None, err_msg
        self.signout()

    @with_context
    def test_user_with_no_more_tasks_find_volunteers(self):
        """Test WEB when a user has contributed to all available tasks, he is
        asked to find new volunteers for a project, if the project is not
        completed yet (overall progress < 100%)"""

        self.register()
        user = User.query.first()
        project = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project)
        taskrun = TaskRunFactory.create(task=task, user=user)
        res = self.app.get('/project/%s/newtask' % project.short_name)

        message = "contributed to all the tasks for this project, but this project still needs more volunteers"
        assert message in str(res.data), (message, str(res.data))
        self.signout()

    @with_context
    def test_user_with_no_more_tasks_find_volunteers_project_completed(self):
        """Test WEB when a user has contributed to all available tasks, he is
        not asked to find new volunteers for a project, if the project is
        completed (overall progress = 100%)"""

        self.register()
        user = User.query.first()
        project = ProjectFactory.create(owner=user)
        task = TaskFactory.create(project=project, n_answers=1)
        taskrun = TaskRunFactory.create(task=task, user=user)
        update_stats(project.id)
        res = self.app.get('/project/%s/newtask' % project.short_name)

        assert task.state == 'completed', task.state
        message = "Sorry, you've contributed to all the tasks for this project, but this project still needs more volunteers, so please spread the word!"
        assert message  not in str(res.data)
        self.signout()

    @with_context
    def test_results(self):
        """Test WEB results shows no data as no template and no data."""
        tr = TaskRunFactory.create()
        project = project_repo.get(tr.project_id)
        url = '/project/%s/results' % project.short_name
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        assert dom.find(id="noresult") is not None, res.data

    @with_context
    def test_results_json(self):
        """Test WEB results shows no data as no template and no data."""
        tr = TaskRunFactory.create()
        project = project_repo.get(tr.project_id)
        url = '/project/%s/results' % project.short_name
        res = self.app_get_json(url)
        data = json.loads(res.data)
        err_msg='data entry missing'
        assert 'n_completed_tasks' in str(data), err_msg
        assert 'n_results' in str(data), err_msg
        assert 'n_task_runs' in str(data), err_msg
        assert 'n_tasks' in str(data), err_msg
        assert 'n_volunteers' in str(data), err_msg
        assert 'overall_progress' in str(data), err_msg
        assert 'owner' in str(data), err_msg
        owner = data['owner']
        assert 'email_addr' not in owner, owner
        assert 'api_key' not in owner, owner
        assert 'created' in owner, err_msg
        assert 'fullname' in owner, err_msg
        assert 'info' in owner, err_msg
        assert 'n_answers' in owner, err_msg
        assert 'name' in owner, err_msg
        assert 'rank' in owner, err_msg
        assert 'registered_ago' in owner, err_msg
        assert 'score' in owner, err_msg
        assert 'pro_features' in str(data), err_msg
        assert 'project' in str(data), err_msg
        project = data['project']
        assert 'secret_key' not in project, project
        assert 'created' in project, err_msg
        assert 'description' in project, err_msg
        assert 'featured' in project, err_msg
        assert 'id' in project, err_msg
        assert 'info' in project, err_msg
        assert 'owner_id' not in project['info'], project['info']
        assert 'last_activity' in project, err_msg
        assert 'last_activity_raw' in project, err_msg
        assert 'n_tasks' in project, err_msg
        assert 'n_volunteers' in project, err_msg
        assert 'name' in project, err_msg
        assert 'overall_progress' in project, err_msg
        assert 'owner' in project, err_msg
        assert 'short_name' in project, err_msg
        assert 'updated' in project, err_msg
        assert data['template']=='/projects/results.html', err_msg
        assert 'title' in str(data), err_msg

    @with_context
    def test_results_with_values(self):
        """Test WEB results with values are not shown as no template but data."""
        task = TaskFactory.create(n_answers=1)
        tr = TaskRunFactory.create(task=task)
        project = project_repo.get(tr.project_id)
        url = '/project/%s/results' % project.short_name
        result = result_repo.get_by(project_id=project.id)
        result.info = dict(foo='bar')
        result_repo.update(result)
        res = self.app.get(url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        assert dom.find(id="noresult") is not None, res.data

    @with_context
    def test_results_with_values_and_template(self):
        """Test WEB results with values and template is shown."""
        task = TaskFactory.create(n_answers=1)
        tr = TaskRunFactory.create(task=task)
        project = project_repo.get(tr.project_id)
        project.info['results'] = "The results"
        project_repo.update(project)
        url = '/project/%s/results' % project.short_name
        result = result_repo.get_by(project_id=project.id)
        result.info = dict(foo='bar')
        result_repo.update(result)
        update_stats(project.id)
        res = self.app.get(url, follow_redirects=True)
        assert "The results" in str(res.data), res.data

    @with_context
    def test_update_project_secret_key_owner(self):
        """Test update project secret key owner."""
        self.register()
        self.new_project()

        project = project_repo.get(1)

        old_key = project.secret_key

        url = "/project/%s/resetsecretkey" % project.short_name

        res = self.app.post(url, follow_redirects=True)

        project = project_repo.get(1)

        err_msg = "A new key should be generated"
        assert "New secret key generated" in str(res.data), err_msg
        assert old_key != project.secret_key, err_msg

    @with_context
    def test_update_project_secret_key_owner_json(self):
        """Test update project secret key owner."""
        self.register()
        self.new_project()

        project = project_repo.get(1)

        old_key = project.secret_key

        csrf_url = "/project/%s/update" % project.short_name
        url = "/project/%s/resetsecretkey" % project.short_name

        res = self.app_get_json(csrf_url)
        data = json.loads(res.data)
        csrf = data['upload_form']['csrf']

        res = self.app_post_json(url, headers={'X-CSRFToken': csrf})
        data = json.loads(res.data)
        assert data['flash'] == 'New secret key generated', data
        assert data['next'] == csrf_url, data
        assert data['status'] == 'success', data

        project = project_repo.get(1)

        err_msg = "A new key should be generated"
        assert "New secret key generated" in str(res.data), err_msg
        assert old_key != project.secret_key, err_msg


    @with_context
    def test_update_project_secret_key_not_owner(self):
        """Test update project secret key not owner."""
        self.register()
        self.new_project()
        self.signout()

        self.register(email="juan@juan.com", name="juanjuan")

        project = project_repo.get(1)

        url = "/project/%s/resetsecretkey" % project.short_name

        res = self.app.post(url, follow_redirects=True)

        assert res.status_code == 403, res.status_code

    @with_context
    def test_update_project_secret_key_not_owner_json(self):
        """Test update project secret key not owner."""
        self.register()
        self.new_project()
        self.signout()

        self.register(email="juan@juan.com", name="juanjuan")

        project = project_repo.get(1)

        url = "/project/%s/resetsecretkey" % project.short_name

        res = self.app_post_json(url)

        assert res.status_code == 403, res.status_code

    @patch('pybossa.view.account.mail_queue')
    @patch('pybossa.otp.OtpAuth')
    @with_context_settings(ENABLE_TWO_FACTOR_AUTH=True)
    def test_otp_signin_signout_json(self, OtpAuth, mail_queue):
        """Test WEB two factor sign in and sign out JSON works"""
        self.register()
        # Log out as the registration already logs in the user
        self.signout()

        res = self.signin(method="GET", content_type="application/json",
                          follow_redirects=False)
        data = json.loads(res.data)
        err_msg = "There should be a form with two keys email & password"
        csrf = data['form'].get('csrf')
        assert data.get('title') == "Sign in", data
        assert 'email' in list(data.get('form').keys()), (err_msg, data)
        assert 'password' in list(data.get('form').keys()), (err_msg, data)

        OTP = '1234'
        otp_secret = OtpAuth.return_value
        otp_secret.totp.return_value = OTP

        res = self.signin(content_type="application/json",
                          csrf=csrf, follow_redirects=True)
        data = json.loads(res.data)
        msg = "an email has been sent to you with one time password"
        err_msg = 'Should redirect to otp validation page'
        otp_secret.totp.assert_called()
        mail_queue.enqueue.assert_called()
        assert data.get('flash') == msg, (err_msg, data)
        assert data.get('status') == SUCCESS, (err_msg, data)
        assert data.get('next').split('/')[-1] == 'otpvalidation', (err_msg, data)

        token = data.get('next').split('/')[-2]

        # pass wrong token
        res = self.otpvalidation(follow_redirects=True, otp=OTP,
                                 content_type='application/json')
        data = json.loads(res.data)
        err_msg = 'Should be error'
        assert data['status'] == 'error', (err_msg, data)
        assert data['flash'] == 'Please sign in.', (err_msg, data)

        # pass wrong otp
        res = self.otpvalidation(token=token, follow_redirects=True,
                                 content_type='application/json')
        data = json.loads(res.data)
        err_msg = 'There should be an invalid OTP error message'
        assert data['status'] == 'error', (err_msg, data)
        msg = 'Invalid one time password, a newly generated one time password was sent to your email.'
        assert data['flash'] == msg, (err_msg, data)

        # pass right otp
        res = self.otpvalidation(token=token, follow_redirects=True, otp=OTP,
                                 content_type='application/json')
        data = json.loads(res.data)
        err_msg = 'There should not be an invalid OTP error message'
        assert data['status'] == 'success', (err_msg, data)

        # Log out
        res = self.signout(content_type="application/json",
                           follow_redirects=False)
        msg = "You are now signed out"
        data = json.loads(res.data)
        assert data.get('flash') == msg, (msg, data)
        assert data.get('status') == SUCCESS, data
        assert data.get('next') == '/', data

    @patch('pybossa.view.account.otp.retrieve_user_otp_secret')
    @patch('pybossa.otp.OtpAuth')
    @with_context_settings(ENABLE_TWO_FACTOR_AUTH=True)
    def test_login_expired_otp(self, OtpAuth, retrieve_user_otp_secret):
        """Test expired otp json"""
        self.register()
        # Log out as the registration already logs in the user
        self.signout()

        res = self.signin(method="GET", content_type="application/json",
                          follow_redirects=False)
        data = json.loads(res.data)
        err_msg = "There should be a form with two keys email & password"
        csrf = data['form'].get('csrf')
        assert data.get('title') == "Sign in", data
        assert 'email' in list(data.get('form').keys()), (err_msg, data)
        assert 'password' in list(data.get('form').keys()), (err_msg, data)

        OTP = '1234'
        otp_secret = OtpAuth.return_value
        otp_secret.totp.return_value = OTP
        retrieve_user_otp_secret.return_value = None

        res = self.signin(content_type="application/json",
                          csrf=csrf, follow_redirects=True)
        data = json.loads(res.data)

        token = data.get('next').split('/')[-2]

        # pass otp - mock expired
        res = self.otpvalidation(token=token, follow_redirects=True, otp=OTP,
                                 content_type='application/json')
        data = json.loads(res.data)
        err_msg = 'OTP should be expired'
        assert data['status'] == ERROR, (err_msg, data)
        assert 'Expired one time password' in data.get('flash'), (err_msg, data)

    @with_context
    @patch('pybossa.view.projects.rank', autospec=True)
    def test_project_index_sorting(self, mock_rank):
        """Test WEB Project index parameters passed for sorting."""
        self.register()
        self.create()
        project = db.session.query(Project).get(1)

        order_by = 'n_volunteers'
        desc = True
        query = 'orderby=%s&desc=%s' % (order_by, desc)

        # Test named category
        url = 'project/category/%s?%s' % (Fixtures.cat_1, query)
        self.app.get(url, follow_redirects=True)
        assert mock_rank.call_args_list[0][0][0][0]['name'] == project.name
        assert mock_rank.call_args_list[0][0][1] == order_by
        assert mock_rank.call_args_list[0][0][2] == desc

        # Test featured
        project.featured = True
        project_repo.save(project)
        url = 'project/category/featured?%s' % query
        self.app.get(url, follow_redirects=True)
        assert mock_rank.call_args_list[1][0][0][0]['name'] == project.name
        assert mock_rank.call_args_list[1][0][1] == order_by
        assert mock_rank.call_args_list[1][0][2] == desc

        # Test draft
        project.featured = False
        project.published = False
        project_repo.save(project)
        url = 'project/category/draft/?%s' % query
        res = self.app.get(url, follow_redirects=True)
        assert mock_rank.call_args_list[2][0][0][0]['name'] == project.name
        assert mock_rank.call_args_list[2][0][1] == order_by
        assert mock_rank.call_args_list[2][0][2] == desc

    @with_context
    @patch('pybossa.view.projects.rank', autospec=True)
    def test_project_index_historical_contributions(self, mock_rank):
        self.create()
        user = user_repo.get(2)
        url = 'project/category/historical_contributions?api_key={}'.format(user.api_key)
        with patch.dict(self.flask_app.config, {'HISTORICAL_CONTRIBUTIONS_AS_CATEGORY': True}):
            res = self.app.get(url, follow_redirects=True)
            assert '<h1>Historical Contributions Projects</h1>' in str(res.data)
            assert not mock_rank.called

    @with_context
    def test_export_task_zip_download_anon(self):
        """Test export task with zip download disabled for anon."""
        project = ProjectFactory.create(zip_download=False)
        url = '/project/%s/tasks/export' % project.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 401

    @with_context
    def test_export_task_zip_download_not_owner(self):
        """Test export task with zip download disabled for not owner."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(zip_download=False, owner=owner)
        url = '/project/%s/tasks/export?api_key=%s' % (project.short_name,
                                                       user.api_key)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 403

    @with_context
    def test_export_task_zip_download_owner(self):
        """Test export task with zip download disabled for owner."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(zip_download=False, owner=owner)
        task = TaskFactory.create_batch(3, project=project)
        url = '/project/%s/tasks/export?api_key=%s&type=task&format=csv' % (project.short_name,
                                                       owner.api_key)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code

    @with_context
    def test_export_task_zip_download_admin(self):
        """Test export task with zip download disabled for admin."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(zip_download=False, owner=owner)
        task = TaskFactory.create_batch(3, project=project)
        url = '/project/%s/tasks/export?api_key=%s&type=task&format=csv' % (project.short_name,
                                                       admin.api_key)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code

    @with_context
    def test_browse_task_zip_download_anon(self):
        """Test browse task with zip download disabled for anon."""
        project = ProjectFactory.create(zip_download=False)
        url = '/project/%s/tasks/browse' % project.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 401

    @with_context
    def test_browse_task_zip_download_not_owner(self):
        """Test browse task with zip download disabled for not owner."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(zip_download=False, owner=owner)
        url = '/project/%s/tasks/browse?api_key=%s' % (project.short_name,
                                                       user.api_key)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 403

    @with_context
    def test_browse_task_zip_download_owner(self):
        """Test browse task with zip download disabled for owner."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(zip_download=False, owner=owner)
        task = TaskFactory.create_batch(20, project=project)
        url = '/project/%s/tasks/browse?api_key=%s' % (project.short_name,
                                                       owner.api_key)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code

    @with_context
    def test_browse_task_zip_download_admin(self):
        """Test browse task with zip download disabled for admin."""
        admin, owner, user = UserFactory.create_batch(3)
        project = ProjectFactory.create(zip_download=False, owner=owner)
        task = TaskFactory.create_batch(20, project=project)
        url = '/project/%s/tasks/browse?api_key=%s' % (project.short_name,
                                                       admin.api_key)
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code

    @with_context
    def test_projects_account(self):
        """Test projecs on profiles are good."""
        owner, contributor = UserFactory.create_batch(2)
        info = dict(passwd_hash='foo', foo='bar')
        project = ProjectFactory.create(owner=owner, info=info)
        TaskRunFactory.create(project=project, user=contributor)

        url = '/account/%s/' % contributor.name
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert 'projects' in list(data.keys()), list(data.keys())
        assert len(data['projects']) == 1, len(data['projects'])
        tmp = data['projects'][0]
        for key in list(info.keys()):
            assert key not in list(tmp['info'].keys())

        url = '/account/%s/' % owner.name
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert len(data['projects']) == 0, len(data['projects'])
        assert 'projects_created' in list(data.keys()), list(data.keys())
        assert len(data['projects_created']) == 1, len(data['projects_created'])
        tmp = data['projects_created'][0]
        for key in list(info.keys()):
            assert key not in list(tmp['info'].keys())

        url = '/account/%s/?api_key=%s' % (owner.name,
                                           owner.api_key)
        res = self.app_get_json(url)
        data = json.loads(res.data)
        assert 'projects_published' in list(data.keys()), list(data.keys())
        assert len(data['projects_published']) == 1, len(data['projects_published'])
        tmp = data['projects_published'][0]
        for key in list(info.keys()):
            assert key in list(tmp['info'].keys())

    @with_context
    @patch('pybossa.view.account.mail_queue', autospec=True)
    @patch('pybossa.view.account.render_template')
    @patch('pybossa.view.account.signer')
    def test_register_with_upref_mdata(self, signer, render, queue):
        """Test WEB register user with user preferences set"""
        from flask import current_app
        import pybossa.core
        current_app.config.upref_mdata = True

        pybossa.core.upref_mdata_choices = dict(languages=[("en", "en"), ("sp", "sp")],
                                    locations=[("us", "us"), ("uk", "uk")],
                                    timezones=[("", ""), ("ACT", "Australia Central Time")],
                                    user_types=[("Researcher", "Researcher"), ("Analyst", "Analyst")])

        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        data = dict(fullname="AJohn Doe", name="johndoe",
                    password="p4ssw0rd", confirm="p4ssw0rd",
                    email_addr="johndoe@example.com",
                    consent=True, user_type="Analyst",
                    languages="sp", locations="uk",
                    timezone="")
        signer.dumps.return_value = ''
        render.return_value = ''
        res = self.app.post('/account/register', data=data, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert res.mimetype == 'text/html', res
        user = user_repo.get_by(name='johndoe')
        assert user.consent, user
        assert user.name == 'johndoe', user
        assert user.email_addr == 'johndoe@example.com', user
        expected_upref = dict(languages=['sp'], locations=['uk'])

        assert user.user_pref == expected_upref, "User preferences did not matched"

        upref_data = dict(languages="en", locations="us",
                        user_type="Researcher", timezone="ACT",
                        work_hours_from="10:00", work_hours_to="17:00",
                        review="user with research experience")
        res = self.app.post('/account/save_metadata/johndoe',
                data=upref_data, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        user = user_repo.get_by(name='johndoe')
        expected_upref = dict(languages=['en'], locations=['us'])
        assert user.user_pref == expected_upref, "User preferences did not matched"

        metadata = user.info['metadata']
        timezone = metadata['timezone']
        work_hours_from = metadata['work_hours_from']
        work_hours_to = metadata['work_hours_to']
        review = metadata['review']
        assert metadata['timezone'] == upref_data['timezone'], "timezone not updated"
        assert metadata['work_hours_from'] == upref_data['work_hours_from'], "work hours from not updated"
        assert metadata['work_hours_to'] == upref_data['work_hours_to'], "work hours to not updated"
        assert metadata['review'] == upref_data['review'], "review not updated"


    @with_context
    @patch('pybossa.view.account.current_user')
    @patch('pybossa.view.account.mail_queue', autospec=True)
    @patch('pybossa.view.account.render_template')
    @patch('pybossa.view.account.signer')
    def test_register_with_invalid_upref_mdata(self, signer, render, queue, current_user):
        """Test WEB register user - invalid user preferences cannot be set"""
        from flask import current_app
        import pybossa.core
        current_app.config.upref_mdata = True

        pybossa.core.upref_mdata_choices = dict(languages=[("en", "en"), ("sp", "sp")],
                                    locations=[("us", "us"), ("uk", "uk")],
                                    timezones=[("", ""), ("ACT", "Australia Central Time")],
                                    user_types=[("Researcher", "Researcher"), ("Analyst", "Analyst")])

        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        data = dict(fullname="AJohn Doe", name="johndoe",
                    password="p4ssw0rd", confirm="p4ssw0rd",
                    email_addr="johndoe@example.com",
                    consent=True, user_type="Analyst",
                    languages="sp", locations="uk",
                    timezone="")
        signer.dumps.return_value = ''
        render.return_value = ''
        res = self.app.post('/account/register', data=data, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert res.mimetype == 'text/html', res
        user = user_repo.get_by(name='johndoe')
        assert user.consent, user
        assert user.name == 'johndoe', user
        assert user.email_addr == 'johndoe@example.com', user
        expected_upref = dict(languages=['sp'], locations=['uk'])
        assert user.user_pref == expected_upref, "User preferences did not matched"

        # update invalid user preferences
        current_user.admin = True
        current_user.id = 999
        upref_invalid_data = dict(languages="ch", locations="jp",
            user_type="Researcher", timezone="ACT",
            work_hours_from="10:00", work_hours_to="17:00",
            review="user with research experience")
        res = self.app.post('/account/save_metadata/johndoe',
                data=upref_invalid_data, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        user = user_repo.get_by(name='johndoe')
        invalid_upref = dict(languages=['ch'], locations=['jp'])
        assert user.user_pref != invalid_upref, "Invalid preferences should not be updated"

    @with_context
    @patch('pybossa.view.account.send_mail', autospec=True)
    @patch('pybossa.view.account.mail_queue', autospec=True)
    @patch('pybossa.view.account.render_template')
    @patch('pybossa.view.account.signer')
    def test_validate_email_once(self, signer, render, queue, send_mail):
        """Test validate email only once."""
        from flask import current_app
        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = False
        user = UserFactory.create()
        signer.dumps.return_value = ''
        render.return_value = ''
        url = '/account/{}/update?api_key={}'.format(user.name, user.api_key)
        data = {'id': user.id, 'fullname': user.fullname,
                'name': user.name,
                'locale': user.locale,
                'email_addr': 'new@fake.com',
                'btn': 'Profile'}
        res = self.app.post(url, data=data, follow_redirects=True)

        current_app.config['ACCOUNT_CONFIRMATION_DISABLED'] = True
        assert 'Use a valid email account' in str(res.data), res.data
