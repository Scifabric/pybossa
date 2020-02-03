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
from default import with_context
from helper import web
from mock import patch
from factories import CategoryFactory
from pybossa.messages import *
from pybossa.core import project_repo


class TestJsonProject(web.Helper):

    def setUp(self):
        super(TestJsonProject, self).setUp()
        CategoryFactory.create()

    @with_context
    def test_project_new_anon(self):
        """Test JSON PROJECT (GET/POST) New works."""
        url = '/project/new'
        res = self.app_get_json(url, follow_redirects=True)
        assert "Sign in" in str(res.data), res.data
        res = self.app_post_json(url, follow_redirects=True)
        assert "Sign in" in str(res.data), res.data

    @with_context
    def test_project_new_auth(self):
        """Test JSON PROJECT (GET/POST) New works."""
        with patch.dict(self.flask_app.config, {'WTF_CSRF_ENABLED': True}):
            self.register()
            url = '/project/new'
            res = self.app_get_json(url, follow_redirects=True)
            data = json.loads(res.data)
            keys = sorted(['errors', 'form', 'template', 'title'])
            assert keys == sorted(data.keys()), data
            assert data.get('form').get('csrf') is not None, data

            # With errors and NOT CSRF
            res = self.app_post_json(url, follow_redirects=True)
            data = json.loads(res.data)
            assert data.get('code') == 400, data
            assert data.get('description') == 'CSRF validation failed.', data

            # With errors and CSRF
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf})
            data = json.loads(res.data)
            assert data.get('errors'), data
            assert len(data.get('form').get('errors').get('name')) == 1, data
            assert len(data.get('form').get('errors').get('short_name')) == 1, data
            assert len(data.get('form').get('errors').get('long_description')) == 1, data

            # New Project
            project = dict(name='project1', short_name='project1', long_description='lore ipsum')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') == SUCCESS, data
            url_next = '/project/%s/update' % project['short_name']
            assert data.get('next') == url_next, data
            db_project = project_repo.get(1)
            err_msg = "It should be the same project"
            assert db_project.name == project['name'], err_msg

            # New Project and wrong CSRF
            project = dict(name='project1', short_name='project1', long_description='lore ipsum')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': 'random'}, data=project)
            data = json.loads(res.data)
            assert data.get('code') == 400, data
