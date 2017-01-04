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

from default import Test, db, with_context
from nose.tools import assert_raises
from mock import patch
from pybossa.model.project import Project
from pybossa.model.user import User
from sqlalchemy.exc import IntegrityError
from factories import ProjectFactory


class TestModelProject(Test):

    @with_context
    def test_project_errors(self):
        """Test project model errors."""
        project = Project(name='Project',
                  short_name='proj',
                  description='desc',
                  owner_id=None)

        # Project.owner_id should not be nullable
        db.session.add(project)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # Project.name should not be nullable
        user = User(email_addr="john.doe@example.com",
                    name="johndoe",
                    fullname="John Doe",
                    locale="en")
        db.session.add(user)
        db.session.commit()
        user = db.session.query(User).first()
        project.owner_id = user.id
        project.name = None
        db.session.add(project)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        project.name = ''
        db.session.add(project)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # Project.short_name should not be nullable
        project.name = "Project"
        project.short_name = None
        db.session.add(project)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        project.short_name = ''
        db.session.add(project)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # Project.description should not be nullable
        db.session.add(project)
        project.short_name = "project"
        project.description = None
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        project.description = ''
        db.session.add(project)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()

        # Project.featured should not be nullable
        project.description = 'description'
        project.featured = None
        db.session.add(project)
        assert_raises(IntegrityError, db.session.commit)
        db.session.rollback()


    def test_needs_password_no_password_key(self):
        """Test needs_password returns false if the project has not a password"""
        project = ProjectFactory.build(info={})

        assert project.needs_password() is False


    @patch('pybossa.model.project.signer')
    def test_needs_password_empty_password_key(self, mock_signer):
        """Test needs_password returns false if the project has an empty password"""
        mock_signer.loads = lambda x: x
        project = ProjectFactory.build(info={'passwd_hash': None})

        assert project.needs_password() is False


    @patch('pybossa.model.project.signer')
    def test_needs_password_with_password_key_and_value(self, mock_signer):
        """Test needs_password returns true if the project has a password"""
        mock_signer.loads = lambda x: x
        project = ProjectFactory.build(info={'passwd_hash': 'mypassword'})

        assert project.needs_password() is True


    @patch('pybossa.model.project.signer')
    def test_check_password(self, mock_signer):
        mock_signer.loads = lambda x: x
        project = ProjectFactory.build(info={'passwd_hash': 'mypassword'})

        assert project.check_password('mypassword')


    @patch('pybossa.model.project.signer')
    def test_check_password_bad_password(self, mock_signer):
        mock_signer.loads = lambda x: x
        project = ProjectFactory.build(info={'passwd_hash': 'mypassword'})

        assert not project.check_password('notmypassword')


    def test_has_autoimporter_returns_true_if_autoimporter(self):
        autoimporter = {'type': 'csv', 'csv_url': 'http://fakeurl.com'}
        project = ProjectFactory.build(info={'autoimporter': autoimporter})

        assert project.has_autoimporter() is True


    def test_has_autoimporter_returns_false_if_no_autoimporter(self):
        project = ProjectFactory.build(info={})

        assert project.has_autoimporter() is False


    def test_get_autoimporter_returns_autoimporter(self):
        autoimporter = {'type': 'csv', 'csv_url': 'http://fakeurl.com'}
        project = ProjectFactory.build(info={'autoimporter': autoimporter})

        assert project.get_autoimporter() == autoimporter, project.get_autoimporter()


    def test_set_autoimporter_works_as_expected(self):
        autoimporter = {'type': 'csv', 'csv_url': 'http://fakeurl.com'}
        project = ProjectFactory.build(info={})
        assert project.has_autoimporter() is False

        project.set_autoimporter(autoimporter)

        assert project.get_autoimporter() == autoimporter, project.get_autoimporter()


    def test_delete_autoimporter_works_as_expected(self):
        autoimporter = {'type': 'csv', 'csv_url': 'http://fakeurl.com'}
        project = ProjectFactory.build(info={'autoimporter': autoimporter})
        assert project.has_autoimporter() is True

        project.delete_autoimporter()

        assert project.has_autoimporter() is False, project.get_autoimporter()
