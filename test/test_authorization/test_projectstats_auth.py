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

from default import Test, assert_not_raises, with_context
from pybossa.auth import ensure_authorized_to
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user
from factories import ProjectFactory, UserFactory
from pybossa.model.project_stats import ProjectStats
import pybossa.cache.project_stats as stats


class TestProjectStatsAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)

    def prepare_stats(self):
      project = ProjectFactory.create()
      stats.update_stats(project.id)
      return stats.get_stats(project.id, full=True)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_can_read_projectstats(self):
        """Test anonymous users can read projectstats"""
        ps = self.prepare_stats()
        assert_not_raises(Exception, ensure_authorized_to, 'read', ps)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_can_read_projectstats(self):
        """Test authenticated users can read projectstats"""
        ps = self.prepare_stats()
        assert_not_raises(Exception, ensure_authorized_to, 'read', ps)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_user_can_read_projectstats(self):
        """Test admin users can read projectstats"""
        ps = self.prepare_stats()
        assert_not_raises(Exception, ensure_authorized_to, 'read', ps)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_crud_projectstats(self):
        """Test anonymous users cannot crud projectstats"""
        ps = self.prepare_stats()
        assert_raises(Unauthorized, ensure_authorized_to, 'create', ps)
        assert_raises(Unauthorized, ensure_authorized_to, 'update', ps)
        assert_raises(Unauthorized, ensure_authorized_to, 'delete', ps)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_cannot_crud_projectstats(self):
        """Test authenticated users cannot crud project stats"""
        ps = self.prepare_stats()
        assert_raises(Forbidden, ensure_authorized_to, 'create', ps)
        assert_raises(Forbidden, ensure_authorized_to, 'update', ps)
        assert_raises(Forbidden, ensure_authorized_to, 'delete', ps)

    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_user_cannot_crud_projectstats(self):
        """Test admin users cannot crud project stats"""
        ps = self.prepare_stats()
        assert_raises(Forbidden, ensure_authorized_to, 'create', ps)
        assert_raises(Forbidden, ensure_authorized_to, 'update', ps)
        assert_raises(Forbidden, ensure_authorized_to, 'delete', ps)
