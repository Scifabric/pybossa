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
        assert "Sign in" in res.data, res.data
        res = self.app_post_json(url, follow_redirects=True)
        assert "Sign in" in res.data, res.data

    @with_context
    def test_project_new_auth(self):
        """Test JSON PROJECT (GET/POST) New works."""
        self.register()
        self.signin()
        with patch.dict(self.flask_app.config, {'WTF_CSRF_ENABLED': True}):
            url = '/project/new'
            res = self.app_get_json(url, follow_redirects=True)
            data = json.loads(res.data)
            keys = sorted(['errors', 'form', 'template', 'title', 'message'])
            assert keys == sorted(data.keys()), data
            assert data.get('form').get('csrf') is not None, data

            # With errors and NOT CSRF
            res = self.app_post_json(url, follow_redirects=True)
            data = json.loads(res.data)
            assert data.get('code') == 400, data
            assert data.get('description') == 'The CSRF token is missing.', data

            # With errors and CSRF
            csrf = self.get_csrf(url)
            print csrf
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf})
            data = json.loads(res.data)
            assert data.get('errors'), data
            assert len(data.get('form').get('errors').get('name')) == 1, data
            assert len(data.get('form').get('errors').get('short_name')) == 1, data
            assert len(data.get('form').get('errors').get('long_description')) == 1, data

            # New Project
            project = dict(name='project1', short_name='project1', long_description='lore ipsum',
                           password='TestPwd1')
            csrf = self.get_csrf(url)
            print csrf
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') == SUCCESS, data
            url_next = '/project/%s/update' % project['short_name']
            assert data.get('next') == url_next, data
            db_project = project_repo.get(1)
            err_msg = "It should be the same project"
            assert db_project.name == project['name'], err_msg

    @with_context
    def test_project_prod_subp_kpi(self):
        """Test PROJECT new/update works for product, subproduct, kpi."""
        self.register()
        self.signin()
        configs = {
            'WTF_CSRF_ENABLED': True,
            'PRODUCTS': {'north', 'south'},
            'SUBPRODUCTS': {'winterfell', 'westeros'}
        }
        with patch.dict(self.flask_app.config, configs):
            # new project
            url = '/project/new'
            project = dict(name='greatwar', short_name='gr8w', long_description='great war',
                           password='NightW1', product='north', subproduct='winterfell', kpi=1)
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') == SUCCESS, data
            proj_repo = project_repo.get(1)
            assert proj_repo.info['product'] == project['product'], 'product has not been set as expected'
            assert proj_repo.info['subproduct'] == project['subproduct'], 'subproduct has not been set as expected'
            assert proj_repo.info['kpi'] == project['kpi'], 'kpi has not been set as expected'

            # update project
            url = '/project/%s/update' % project['short_name']
            project = dict(name='greatwar', description=proj_repo.description, id=proj_repo.id,
                           category_id=proj_repo.category_id, product='south', subproduct='westeros', kpi=2)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') == SUCCESS, data
            proj_repo = project_repo.get(1)
            assert proj_repo.info['product'] == project['product'], 'product has not been set as expected'
            assert proj_repo.info['subproduct'] == project['subproduct'], 'subproduct has not been set as expected'
            assert proj_repo.info['kpi'] == project['kpi'], 'kpi has not been set as expected'

            # incorrect vals results error
            url = '/project/new'
            project = dict(name='greatwar2', short_name='gr8w2', long_description='great war',
                           password='NightW1', product='wrongp', subproduct='wrongsubp', kpi='aa')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            err_msg = {'kpi': ['Not a valid integer value'], 'product': ['Not a valid choice'], 'subproduct': ['Not a valid choice']}
            assert data.get('errors') and data['form']['errors'] == err_msg, data
