# -*- coding: utf8 -*-
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
import json
from mock import patch, MagicMock

from default import db, with_context
from factories import ProjectFactory, UserFactory
from helper import web
from pybossa.repositories import UserRepository, ProjectRepository

project_repo = ProjectRepository(db)
user_repo = UserRepository(db)


class TestProjectWebpushView(web.Helper):

    def setUp(self):
        super(TestProjectWebpushView, self).setUp()
        self.owner = UserFactory.create(email_addr='a@a.com')
        user_repo.save(self.owner)
        self.project = ProjectFactory.create(owner=self.owner, published=False)
        self.url = "/project/%s/webpush" % self.project.short_name

    @with_context
    def test_login_required(self):
        """Test WEB Project view webpush requires login."""

        res = self.app.get(self.url, follow_redirects=True)

        assert "Sign in" in res.data, res.data

    @with_context
    def test_not_owner(self):
        """Test WEB Project view webpush rejects auth user but not owner."""

        self.signout()

        user = UserFactory.create()

        res = self.app.get(self.url + '?api_key=' + user.api_key,
                           follow_redirects=True)

        assert res.status_code == 403, res.status_code

    @with_context
    @patch('pybossa.jobs.PybossaOneSignal')
    def test_owner(self, mock_onesignal):
        """Test WEB Project view webpush requires owner."""
        onesignaldata = {'id': 1, 'basic_auth_key': 'key2'}
        client = MagicMock()
        client.create_app.return_value = (200, 'OK', onesignaldata)
        mock_onesignal.return_value = client

        with patch.dict(self.flask_app.config, {'ONESIGNAL_AUTH_KEY': 'key'}):
            res = self.app.get(self.url + '?api_key=' + self.owner.api_key,
                               follow_redirects=True)

            data = json.loads(res.data)

            assert res.status_code == 200, res.status_code
            assert 'id' in data.keys(), data
            assert 'basic_auth_key' in data.keys(), data
            assert data == onesignaldata, data

            pr = project_repo.get(self.project.id)

            assert pr.info['onesignal'], pr.info
            assert pr.info['onesignal']['basic_auth_key'] == 'key2', pr.info
            assert pr.info['onesignal_app_id'] == 1, pr.info


    @with_context
    @patch('pybossa.jobs.PybossaOneSignal')
    def test_admin(self, mock_onesignal):
        """Test WEB Project view webpush requires admin."""
        admin = UserFactory.create(admin=True)
        onesignaldata = {'id': 1, 'basic_auth_key': 'key2'}
        client = MagicMock()
        client.create_app.return_value = (200, 'OK', onesignaldata)
        mock_onesignal.return_value = client

        with patch.dict(self.flask_app.config, {'ONESIGNAL_AUTH_KEY': 'key'}):
            res = self.app.get(self.url + '?api_key=' + admin.api_key,
                               follow_redirects=True)

            data = json.loads(res.data)

            assert res.status_code == 200, res.status_code
            assert 'id' in data.keys(), data
            assert 'basic_auth_key' in data.keys(), data
            assert data == onesignaldata, data

            pr = project_repo.get(self.project.id)

            assert pr.info['onesignal'], pr.info
            assert pr.info['onesignal']['basic_auth_key'] == 'key2', pr.info
            assert pr.info['onesignal_app_id'] == 1, pr.info
