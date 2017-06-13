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
from factories import ProjectFactory, UserFactory, AuditlogFactory
from pybossa.model.auditlog import Auditlog



class TestAuditlogAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)



    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_read_auditlog(self):
        """Test anonymous users cannot read an auditlog"""

        log = AuditlogFactory.create()

        assert_raises(Unauthorized, ensure_authorized_to, 'read', log)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_read_project_auditlogs(self):
        """Test anonymous users cannot read auditlogs of a specific project"""

        project = ProjectFactory.create()

        assert_raises(Unauthorized, ensure_authorized_to, 'read', Auditlog, project_id=project.id)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_user_cannot_read_auditlog(self):
        """Test owner users can read an auditlog"""

        owner = UserFactory.create_batch(2)[1]
        project = ProjectFactory.create(owner=owner)
        log = AuditlogFactory.create(project_id=project.id)

        assert self.mock_authenticated.id == project.owner_id

        assert_not_raises(Exception, ensure_authorized_to, 'read', log)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_owner_user_cannot_read_project_auditlogs(self):
        """Test owner users can read auditlogs of a specific project"""

        owner = UserFactory.create_batch(2)[1]
        project = ProjectFactory.create(owner=owner)

        assert_not_raises(Exception, ensure_authorized_to, 'read', Auditlog, project_id=project.id)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_user_can_read_auditlog(self):
        """Test admin users can read an auditlog"""

        owner = UserFactory.create_batch(2)[1]
        project = ProjectFactory.create(owner=owner)
        log = AuditlogFactory.create(project_id=project.id)

        assert self.mock_admin.id != project.owner_id
        assert_not_raises(Exception, ensure_authorized_to, 'read', log)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_user_can_read_project_auditlogs(self):
        """Test admin users can read auditlogs from a project"""

        owner = UserFactory.create_batch(2)[1]
        project = ProjectFactory.create(owner=owner)

        assert self.mock_admin.id != project.owner_id
        assert_not_raises(Exception, ensure_authorized_to, 'read', Auditlog, project_id=project.id)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_crud_auditlog(self):
        """Test anonymous users cannot crud auditlogs"""

        log = Auditlog()

        assert_raises(Unauthorized, ensure_authorized_to, 'create', log)
        assert_raises(Unauthorized, ensure_authorized_to, 'update', log)
        assert_raises(Unauthorized, ensure_authorized_to, 'delete', log)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_authenticated)
    def test_authenticated_user_cannot_crud_auditlog(self):
        """Test authenticated users cannot crud auditlogs"""

        log = Auditlog()

        assert_raises(Forbidden, ensure_authorized_to, 'create', log)
        assert_raises(Forbidden, ensure_authorized_to, 'update', log)
        assert_raises(Forbidden, ensure_authorized_to, 'delete', log)


    @with_context
    @patch('pybossa.auth.current_user', new=mock_admin)
    def test_admin_user_cannot_crud_auditlog(self):
        """Test admin users cannot crud auditlogs"""

        log = Auditlog()

        assert_raises(Forbidden, ensure_authorized_to, 'create', log)
        assert_raises(Forbidden, ensure_authorized_to, 'update', log)
        assert_raises(Forbidden, ensure_authorized_to, 'delete', log)
