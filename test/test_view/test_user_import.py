# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric
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
from StringIO import StringIO
from bs4 import BeautifulSoup

from default import db, with_context
from factories import UserFactory
from helper import web
from mock import patch
from pybossa.repositories import UserRepository


user_repo = UserRepository(db)


def map_diag(l):
    return [(x, x) for x in l]


choices = {
    'languages': map_diag(['lang_a', 'lang_b']),
    'locations': map_diag(['loc_a', 'loc_b']),
    'timezones': map_diag(['', 'tz_a', 'tz_b']),
    'user_types': map_diag(['type_a', 'type_b'])
}


class TestUserImport(web.Helper):

    @with_context
    def test_not_allowed(self):
        url = '/admin/userimport'
        res = self.app.get(url, follow_redirects=True)
        assert 'This feature requires being logged in' in res.data

    @with_context
    def test_allowed(self):
        admin = UserFactory.create()

        url = '/admin/userimport?api_key=%s&type=%s' % (admin.api_key, 'usercsvimport')
        res = self.app.get(url, follow_redirects=True)
        soup = BeautifulSoup(res.data)
        form = soup.form
        assert form.attrs['action'] == '/admin/userimport'


    @with_context
    def test_post_no_file(self):
        admin = UserFactory.create()

        url = '/admin/userimport?api_key=%s&type=%s' % (admin.api_key, 'usercsvimport')
        res = self.app.post(url, follow_redirects=True)
        assert 'No file' in res.data

    @with_context
    @patch('pybossa.forms.forms.app_settings.upref_mdata.get_upref_mdata_choices')
    @patch('pybossa.cache.task_browse_helpers.app_settings.upref_mdata')
    def test_post(self, upref_mdata, get_upref_mdata_choices):
        upref_mdata = True
        get_upref_mdata_choices.return_value = choices

        self.register()
        self.signin()
        url = '/admin/userimport?type=%s' % 'usercsvimport'
        users = '''name,fullname,email_addr,password,project_slugs,user_pref,metadata
            newuser,New User,new@user.com,NewU$3r!,,{},{"user_type": "type_a"}'''
        res = self.app.post(url, follow_redirects=True, content_type='multipart/form-data',
            data={'file': (StringIO(users), 'users.csv')})
        assert '1 new users were imported successfully' in res.data, res.data

        new_user = user_repo.get_by_name('newuser')
        assert new_user.fullname == 'New User'
        assert new_user.email_addr == 'new@user.com'
        assert new_user.info['metadata']['user_type'] == 'type_a'

    @with_context
    @patch('pybossa.forms.forms.app_settings.upref_mdata.get_upref_mdata_choices')
    @patch('pybossa.cache.task_browse_helpers.app_settings.upref_mdata')
    def test_invalid_data(self, upref_mdata, get_upref_mdata_choices):
        upref_mdata = True
        get_upref_mdata_choices.return_value = choices

        self.register()
        self.signin()
        url = '/admin/userimport?type=%s' % 'usercsvimport'
        users = '''name,fullname,email_addr,password,project_slugs,user_pref,metadata
            newuser,New User,new@user.com,NewU$3r!,,{},{"user_type": "type_c"}'''
        res = self.app.post(url, follow_redirects=True, content_type='multipart/form-data',
            data={'file': (StringIO(users), 'users.csv')})
        assert 'It looks like there were no new users created' in res.data, res.data

    @with_context
    @patch('pybossa.forms.forms.app_settings.upref_mdata.get_upref_mdata_choices')
    @patch('pybossa.cache.task_browse_helpers.app_settings.upref_mdata')
    def test_invalid_metadata(self, upref_mdata, get_upref_mdata_choices):
        upref_mdata = True
        get_upref_mdata_choices.return_value = choices

        self.register()
        self.signin()
        from pybossa import core

        url = '/admin/userimport?type=%s' % 'usercsvimport'
        users = '''name,fullname,email_addr,password,project_slugs,user_pref,metadata
            newuser,New User,new@user.com,NewU$3r!,,{},{}'''
        res = self.app.post(url, follow_redirects=True, content_type='multipart/form-data',
            data={'file': (StringIO(users), 'users.csv')})
        assert 'Missing user_type in metadata' in res.data, res.data
