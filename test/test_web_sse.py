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
from helper import web
from default import with_context
from factories import ProjectFactory
from pybossa.core import user_repo
from pybossa.view.projects import project_event_stream
from mock import patch, MagicMock


class TestWebSse(web.Helper):

    fake_sse_response = b"data: This is the first message.\n\n"

    @with_context
    def test_stream_uri_private_anon(self):
        """Test stream URI private anon works."""
        project = ProjectFactory.create()
        private_uri = '/project/%s/privatestream' % project.short_name
        res = self.app.get(private_uri, follow_redirects=True)
        assert res.status_code == 200, res.status_code
        assert 'Please sign in to access this page' in str(res.data), res.data

    @with_context
    def test_stream_uri_private_auth(self):
        """Test stream URI private auth but not owner works."""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        self.signout()
        self.register(fullname='Juan', name='juan', password='juana')
        private_uri = '/project/%s/privatestream' % project.short_name
        res = self.app.get(private_uri, follow_redirects=True)
        assert res.status_code == 403, res.data

    @with_context
    @patch('pybossa.view.projects.project_event_stream')
    @patch('flask.Response', autospec=True)
    def test_stream_uri_private_owner(self, mock_response, mock_sse):
        """Test stream URI private owner works."""
        mock_sse.return_value = self.fake_sse_response
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        private_uri = '/project/%s/privatestream' % project.short_name
        self.app.get(private_uri, follow_redirects=True)
        assert mock_sse.called
        assert mock_sse.called_once_with(project.short_name, 'private')

    @with_context
    def test_stream_uri_private_owner_404(self):
        """Test stream URI private return 404 when SSE disabled
        for owner works."""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        private_uri = '/project/%s/privatestream' % project.short_name
        with patch.dict(self.flask_app.config, {'SSE': False}):
            res = self.app.get(private_uri, follow_redirects=True)
            assert res.status_code == 404


    @with_context
    @patch('pybossa.view.projects.project_event_stream')
    @patch('flask.Response', autospec=True)
    def test_stream_uri_private_admin(self, mock_response, mock_sse):
        """Test stream URI private admin but not owner works."""
        mock_sse.return_value = self.fake_sse_response
        self.register()
        self.signout()
        self.register(fullname="name", name="name")
        user = user_repo.get(2)
        project = ProjectFactory.create(owner=user)
        private_uri = '/project/%s/privatestream' % project.short_name
        self.signout()
        # Sign in as admin
        self.signin()
        res = self.app.get(private_uri, follow_redirects=True)
        assert mock_sse.called
        assert mock_sse.called_once_with(project.short_name, 'private')
        assert res.status_code == 200
        assert res.data == self.fake_sse_response, res.data

    @with_context
    def test_stream_uri_private_admin_404(self):
        """Test stream URI private returns 404 when sse disabled for
        admin but not owner works."""
        with patch.dict(self.flask_app.config, {'SSE': False}):
            self.register()
            self.signout()
            self.register(fullname="name", name="name")
            user = user_repo.get(2)
            project = ProjectFactory.create(owner=user)
            private_uri = '/project/%s/privatestream' % project.short_name
            self.signout()
            # Sign in as admin
            self.signin()
            res = self.app.get(private_uri, follow_redirects=True)
            assert res.status_code == 404


    @with_context
    @patch('pybossa.view.projects.project_event_stream')
    @patch('flask.Response', autospec=True)
    def test_stream_uri_public_admin(self, mock_response, mock_sse):
        """Test stream URI public admin but not owner works."""
        mock_sse.return_value = self.fake_sse_response
        self.register()
        self.signout()
        self.register(fullname="name", name="name")
        user = user_repo.get(2)
        project = ProjectFactory.create(owner=user)
        private_uri = '/project/%s/publicstream' % project.short_name
        self.signout()
        # Sign in as admin
        self.signin()
        res = self.app.get(private_uri, follow_redirects=True)
        assert mock_sse.called
        assert mock_sse.called_once_with(project.short_name, 'public')
        assert res.status_code == 200
        assert res.data == self.fake_sse_response, res.data

    @with_context
    @patch('pybossa.view.projects.project_event_stream')
    @patch('flask.Response', autospec=True)
    def test_stream_uri_public_owner(self, mock_response, mock_sse):
        """Test stream URI public owner works."""
        mock_sse.return_value = self.fake_sse_response
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        private_uri = '/project/%s/publicstream' % project.short_name
        self.app.get(private_uri, follow_redirects=True)
        assert mock_sse.called
        assert mock_sse.called_once_with(project.short_name, 'public')

    @with_context
    @patch('pybossa.view.projects.project_event_stream')
    @patch('flask.Response', autospec=True)
    def test_stream_uri_public_anon(self, mock_response, mock_sse):
        """Test stream URI public anon works."""
        mock_sse.return_value = self.fake_sse_response
        project = ProjectFactory.create()
        private_uri = '/project/%s/publicstream' % project.short_name
        self.app.get(private_uri, follow_redirects=True)
        assert mock_sse.called
        assert mock_sse.called_once_with(project.short_name, 'public')

    @with_context
    def test_stream_uri_public_404(self, ):
        """Test stream URI public 404 when SSE disabled works."""
        project = ProjectFactory.create()
        private_uri = '/project/%s/publicstream' % project.short_name
        with patch.dict(self.flask_app.config, {'SSE': False}):
            res = self.app.get(private_uri, follow_redirects=True)
            assert res.status_code == 404

    @with_context
    @patch('pybossa.view.projects.project_event_stream')
    @patch('flask.Response', autospec=True)
    def test_stream_uri_public_auth_not_admin_not_owner(self, mock_response,
                                                        mock_sse):
        """Test stream URI public auth but not owner or admin works."""
        mock_sse.return_value = self.fake_sse_response
        self.register()
        self.signout()
        self.register(fullname="name", name="name")
        user = user_repo.get(2)
        project = ProjectFactory.create(owner=user)
        self.signout()
        self.register(fullname="name2", name="name2")
        private_uri = '/project/%s/publicstream' % project.short_name
        res = self.app.get(private_uri, follow_redirects=True)
        assert mock_sse.called
        assert mock_sse.called_once_with(project.short_name, 'public')
        assert res.status_code == 200
        assert res.data == self.fake_sse_response, res.data

    @patch('pybossa.view.projects.sentinel.master.pubsub')
    def test_project_event_stream(self, mock_pubsub):
        """Test project_event_stream works."""
        tmp = MagicMock()
        def gen():
            yield dict(data='foobar')
        tmp.listen.return_value = gen()
        mock_pubsub.return_value = tmp
        res = project_event_stream('foo', 'public')
        expected = 'data: %s\n\n' % 'foobar'
        assert next(res) == expected, next(res)
