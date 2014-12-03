# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

from default import Test, assert_not_raises
from pybossa.auth import require
from nose.tools import assert_raises
from werkzeug.exceptions import Forbidden, Unauthorized
from mock import patch
from test_authorization import mock_current_user
from factories import AppFactory, BlogpostFactory, UserFactory
from factories import reset_all_pk_sequences
from pybossa.core import project_repo, auditlog_repo



class TestAuditlogAuthorization(Test):

    mock_anonymous = mock_current_user()
    mock_authenticated = mock_current_user(anonymous=False, admin=False, id=2)
    mock_admin = mock_current_user(anonymous=False, admin=True, id=1)



    @patch('pybossa.auth.current_user', new=mock_anonymous)
    @patch('pybossa.auth.blogpost.current_user', new=mock_anonymous)
    def test_anonymous_user_cannot_read_auditlog(self):
        """Test anonymous users cannot read auditlogs"""

        app = AppFactory.create()
        app.hidden = 1
        project_repo.update(app)

        logs = auditlog_repo.filter_by(app_short_name=app.short_name)

        for log in logs:
            assert_raises(Unauthorized, getattr(require, 'auditlog').read, log)

    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_owner_user_cannot_read_auditlog(self):
        """Test owner users cannot read auditlogs"""

        owner = UserFactory.create_batch(2)[1]
        app = AppFactory.create(owner=owner)
        app.hidden = 1
        project_repo.update(app)

        logs = auditlog_repo.filter_by(app_short_name=app.short_name)

        assert self.mock_authenticated.id == app.owner_id

        for log in logs:
            assert_raises(Unauthorized, getattr(require, 'auditlog').read, log)

    @patch('pybossa.auth.current_user', new=mock_authenticated)
    @patch('pybossa.auth.blogpost.current_user', new=mock_authenticated)
    def test_pro_user_can_read_auditlog(self):
        """Test pro users can read auditlogs"""

        owner = UserFactory.create_batch(2, pro=True)[1]
        app = AppFactory.create(owner=owner)
        app.hidden = 1
        project_repo.update(app)

        logs = auditlog_repo.filter_by(app_short_name=app.short_name)

        assert self.mock_authenticated.id == app.owner_id

        for log in logs:
            assert_not_raises(Exception, getattr(require, 'auditlog').read, log)



    @patch('pybossa.auth.current_user', new=mock_admin)
    @patch('pybossa.auth.blogpost.current_user', new=mock_admin)
    def test_admin_user_can_read_auditlog(self):
        """Test admin users can read auditlogs"""

        owner = UserFactory.create_batch(2)[1]
        app = AppFactory.create(owner=owner)
        app.hidden = 1
        project_repo.update(app)

        logs = auditlog_repo.filter_by(app_short_name=app.short_name)

        for log in logs:
            assert_not_raises(Exception, getattr(require, 'auditlog').read, log)
