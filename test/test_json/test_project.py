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
from pybossa.api.user import data_access
from pybossa.forms.forms import ProjectForm


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
            keys = sorted(['errors', 'form', 'template', 'title', 'prodsubprods', 'project'])
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
                           password='TestPwd1', product='abc', subproduct='def', kpi=0.5,
                           input_data_class='L4 - public', output_data_class='L4 - public')
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
            'PRODUCTS_SUBPRODUCTS': {
                'north': ['winterfell'],
                'west': ['westeros']
            }
        }
        with patch.dict(self.flask_app.config, configs):
            # new project
            url = '/project/new'
            project = dict(name='greatwar', short_name='gr8w', long_description='great war',
                           password='NightW1', product='north', subproduct='winterfell', kpi=1,
                           input_data_class='L4 - public', output_data_class='L4 - public')
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
                           category_id=proj_repo.category_id, product='west', subproduct='westeros', kpi=2,
                           input_data_class='L4 - public', output_data_class='L4 - public')
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
                           password='NightW1', product='wrongp', subproduct='wrongsubp', kpi='aa',
                           input_data_class='L4 - public', output_data_class='L4 - public')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            err_msg = {'kpi': ['This field is required.'], 'product': ['Not a valid choice'], 'subproduct': ['Not a valid choice']}
            assert data.get('errors') and data['form']['errors'] == err_msg, data

    @with_context
    def test_project_kpi_range_valid(self):
        """Test PROJECT valid kpi range thresholds."""
        self.register()
        self.signin()
        configs = {
            'WTF_CSRF_ENABLED': True,
            'PRODUCTS_SUBPRODUCTS': {
                'north': ['winterfell'],
                'west': ['westeros']
            }
        }
        with patch.dict(self.flask_app.config, configs):
            # Valid kpi at minimum threshold of 0.1.
            url = '/project/new'
            project = dict(name='kpimin', short_name='kpimin', long_description='kpimin',
                           password='NightW1', product='north', subproduct='winterfell', kpi=0.1,
                           input_data_class='L4 - public', output_data_class='L4 - public')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') == SUCCESS, data
            proj_repo = project_repo.get(1)
            assert proj_repo.info['kpi'] == project['kpi'], 'kpi is valid'

            # Valid kpi at maximum threshold of 120.
            url = '/project/new'
            project = dict(name='kpimax', short_name='kpimax', long_description='kpimax',
                           password='NightW1', product='north', subproduct='winterfell', kpi=120,
                           input_data_class='L4 - public', output_data_class='L4 - public')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') == SUCCESS, data
            proj_repo = project_repo.get(2)
            assert proj_repo.info['kpi'] == project['kpi'], 'kpi is valid'

    @with_context
    def test_project_kpi_two_decimals_valid(self):
        """Test PROJECT valid kpi with 2 decimal places."""
        self.register()
        self.signin()
        configs = {
            'WTF_CSRF_ENABLED': True,
            'PRODUCTS_SUBPRODUCTS': {
                'north': ['winterfell'],
                'west': ['westeros']
            }
        }
        with patch.dict(self.flask_app.config, configs):
            # Valid kpi with 2 decimal places.
            url = '/project/new'
            project = dict(name='kpitwodecimals', short_name='kpitwodecimals', long_description='kpitwodecimals',
                           password='NightW1', product='north', subproduct='winterfell', kpi=0.16,
                           input_data_class='L4 - public', output_data_class='L4 - public')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') == SUCCESS, data
            proj_repo = project_repo.get(1)
            assert proj_repo.info['kpi'] == project['kpi'], 'kpi is valid'

    @with_context
    def test_project_kpi_range_below_threshold(self):
        """Test PROJECT invalid kpi range below threshold."""
        self.register()
        self.signin()
        configs = {
            'WTF_CSRF_ENABLED': True,
            'PRODUCTS_SUBPRODUCTS': {
                'north': ['winterfell'],
                'west': ['westeros']
            }
        }
        with patch.dict(self.flask_app.config, configs):
            # Invalid kpi below minimum threshold of 0.1.
            url = '/project/new'
            project = dict(name='kpibelowmin', short_name='kpibelowmin', long_description='kpibelowmin',
                           password='NightW1', product='north', subproduct='winterfell', kpi=0.01,
                           input_data_class='L4 - public', output_data_class='L4 - public')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') != SUCCESS, data
            proj_repo = project_repo.get(1)
            err_msg = {'kpi': ['Number must be between 0.1 and 120.']}
            assert data.get('errors') and data['form']['errors'] == err_msg, data

    @with_context
    def test_project_kpi_range_above_threshold(self):
        """Test PROJECT invalid kpi range above threshold."""
        self.register()
        self.signin()
        configs = {
            'WTF_CSRF_ENABLED': True,
            'PRODUCTS_SUBPRODUCTS': {
                'north': ['winterfell'],
                'west': ['westeros']
            }
        }
        with patch.dict(self.flask_app.config, configs):
            # Invalid kpi above maximum threshold of 120.
            url = '/project/new'
            project = dict(name='kpiabovemax', short_name='kpiabovemax', long_description='kpiabovemax',
                           password='NightW1', product='north', subproduct='winterfell', kpi=121,
                           input_data_class='L4 - public', output_data_class='L4 - public')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') != SUCCESS, data
            proj_repo = project_repo.get(1)
            err_msg = {'kpi': ['Number must be between 0.1 and 120.']}
            assert data.get('errors') and data['form']['errors'] == err_msg, data

    @with_context
    def test_project_kpi_range_min_threshold(self):
        """Test PROJECT valid kpi range at min threshold."""
        self.register()
        self.signin()
        configs = {
            'WTF_CSRF_ENABLED': True,
            'PRODUCTS_SUBPRODUCTS': {
                'north': ['winterfell'],
                'west': ['westeros']
            }
        }
        with patch.dict(self.flask_app.config, configs):
            # Valid kpi at minimum threshold of 0.1.
            url = '/project/new'
            project = dict(name='kpiabovemax', short_name='kpiabovemax', long_description='kpiabovemax',
                           password='NightW1', product='north', subproduct='winterfell', kpi=0.1,
                           input_data_class='L4 - public', output_data_class='L4 - public')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') == SUCCESS, data
            proj_repo = project_repo.get(1)
            assert proj_repo.info['kpi'] == project['kpi'], 'kpi is valid'

    @with_context
    def test_project_kpi_range_max_threshold(self):
        """Test PROJECT valid kpi range at max threshold."""
        self.register()
        self.signin()
        configs = {
            'WTF_CSRF_ENABLED': True,
            'PRODUCTS_SUBPRODUCTS': {
                'north': ['winterfell'],
                'west': ['westeros']
            }
        }
        with patch.dict(self.flask_app.config, configs):
            """Test PROJECT valid kpi range at max threshold."""
            url = '/project/new'
            project = dict(name='kpiabovemax', short_name='kpiabovemax', long_description='kpiabovemax',
                           password='NightW1', product='north', subproduct='winterfell', kpi=120,
                           input_data_class='L4 - public', output_data_class='L4 - public')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') == SUCCESS, data
            proj_repo = project_repo.get(1)
            assert proj_repo.info['kpi'] == project['kpi'], 'kpi is valid'

    @with_context
    def test_project_kpi_missing_value(self):
        """Test PROJECT missing kpi value."""
        self.register()
        self.signin()
        configs = {
            'WTF_CSRF_ENABLED': True,
            'PRODUCTS_SUBPRODUCTS': {
                'north': ['winterfell'],
                'west': ['westeros']
            }
        }
        with patch.dict(self.flask_app.config, configs):
            # Missing kpi value.
            url = '/project/new'
            project = dict(name='kpiabovemax', short_name='kpiabovemax', long_description='kpiabovemax',
                           password='NightW1', product='north', subproduct='winterfell',
                           input_data_class='L4 - public', output_data_class='L4 - public')
            csrf = self.get_csrf(url)
            res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
            data = json.loads(res.data)
            assert data.get('status') != SUCCESS, data
            proj_repo = project_repo.get(1)
            err_msg = {'kpi': ['This field is required.']}
            assert data.get('errors') and data['form']['errors'] == err_msg, data

    @with_context
    def test_new_project_data_access(self):
        """Test PROJECT data access."""

        self.register()
        self.signin()
        data_access_levels = dict(valid_access_levels=[("King", "King"), ("Queen", "Queen")])

        configs = {
            'WTF_CSRF_ENABLED': True,
            'PRODUCTS_SUBPRODUCTS': {
                'north': ['winterfell'],
                'west': ['westeros']
            },
            'data_access_levels': data_access_levels
        }

        with patch.dict(self.flask_app.config, configs):
            with patch.dict(data_access.data_access_levels, data_access_levels):

                url = '/project/new'
                project = dict(name='kpimin', short_name='kpimin', long_description='kpimin',
                            password='NightW1', product='north', subproduct='winterfell',
                            kpi=0.1, input_data_class='L4 - public', output_data_class='L4 - public')
                csrf = self.get_csrf(url)
                res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
                data = json.loads(res.data)
                assert data.get('status') == SUCCESS, data
                proj_repo = project_repo.get(1)
                assert proj_repo.info['data_classification']['input_data'] == project['input_data_class']
                assert proj_repo.info['data_classification']['output_data'] == project['output_data_class']

                # update project
                url = '/project/%s/update' % project['short_name']
                project = dict(name='greatwar', description=proj_repo.description, id=proj_repo.id,
                            category_id=proj_repo.category_id, product='west', subproduct='westeros', kpi=2,
                            input_data_class='L3 - community', output_data_class='L3 - community')
                res = self.app_post_json(url, headers={'X-CSRFToken': csrf}, data=project)
                data = json.loads(res.data)
                assert data.get('status') == SUCCESS, data
                proj_repo = project_repo.get(1)
                assert proj_repo.info['product'] == project['product'], 'product has not been set as expected'
                assert proj_repo.info['subproduct'] == project['subproduct'], 'subproduct has not been set as expected'
                assert proj_repo.info['kpi'] == project['kpi'], 'kpi has not been set as expected'
                assert proj_repo.info['data_classification']['input_data'] == project['input_data_class'], 'input_data_class has not been set as expected'
                assert proj_repo.info['data_classification']['output_data'] == project['output_data_class'], 'output_data_class has not been set as expected'

