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

from pybossa.core import project_repo
from pybossa.jobs import warn_old_project_owners, get_non_updated_projects
from default import Test, with_context
from factories import ProjectFactory, TaskFactory, UserFactory
from mock import patch, MagicMock


class TestOldProjects(Test):

    @with_context
    def test_get_non_updated_projects_returns_none(self):
        """Test JOB get non updated returns none."""
        projects = get_non_updated_projects()
        err_msg = "There should not be any outdated project."
        assert len(projects) == 0, err_msg


    @with_context
    def test_get_non_updated_projects_returns_one_project(self):
        """Test JOB get non updated returns one project."""
        project = ProjectFactory.create(updated='2010-10-22T11:02:00.000000')
        projects = get_non_updated_projects()
        err_msg = "There should be one outdated project."
        assert len(projects) == 1, err_msg
        assert projects[0].name == project.name, err_msg

    @with_context
    @patch('pybossa.cache.projects.clean')
    @patch('pybossa.core.mail')
    def test_warn_project_owner(self, mail, clean_mock):
        """Test JOB email is sent to warn project owner."""
        # Mock for the send method
        send_mock = MagicMock()
        send_mock.send.return_value = True
        # Mock for the connection method
        connection = MagicMock()
        connection.__enter__.return_value = send_mock
        # Join them
        mail.connect.return_value = connection

        date = '2010-10-22T11:02:00.000000'
        owner = UserFactory.create(consent=True, subscribed=True)
        project = ProjectFactory.create(updated=date, owner=owner)
        project_id = project.id
        warn_old_project_owners()
        project = project_repo.get(project_id)
        err_msg = "mail.connect() should be called"
        assert mail.connect.called, err_msg
        err_msg = "conn.send() should be called"
        assert send_mock.send.called, err_msg
        err_msg = "project.contacted field should be True"
        assert project.contacted, err_msg
        err_msg = "project.published field should be False"
        assert project.published is False, err_msg
        err_msg = "cache of project should be cleaned"
        clean_mock.assert_called_with(project_id), err_msg
        err_msg = "The update date should be different"
        assert project.updated != date, err_msg

    @with_context
    @patch('pybossa.cache.projects.clean')
    @patch('pybossa.core.mail')
    def test_warn_project_owner(self, mail, clean_mock):
        """Test JOB email is sent to warn project owner."""
        from smtplib import SMTPRecipientsRefused
        from nose.tools import assert_raises
        # Mock for the send method
        send_mock = MagicMock()
        send_mock.send.side_effect = SMTPRecipientsRefused('wrong')
        # Mock for the connection method
        connection = MagicMock()
        connection.__enter__.return_value = send_mock
        # Join them
        mail.connect.return_value = connection

        date = '2010-10-22T11:02:00.000000'
        owner = UserFactory.create(consent=True, subscribed=True,
                                   email_addr="wrong")
        project = ProjectFactory.create(updated=date, owner=owner)
        project_id = project.id
        assert warn_old_project_owners() is False
        assert_raises(SMTPRecipientsRefused, send_mock.send, 'msg')
        project = project_repo.get(project_id)
        err_msg = "mail.connect() should be called"
        assert mail.connect.called, err_msg
        err_msg = "conn.send() should be called"
        assert send_mock.send.called, err_msg
        err_msg = "project.contacted field should be False"
        assert project.contacted is False, err_msg
        err_msg = "project.published field should be True"
        assert project.published, err_msg
        err_msg = "The update date should be the same"
        assert project.updated == date, err_msg

    @with_context
    @patch('pybossa.cache.projects.clean')
    @patch('pybossa.core.mail')
    def test_warn_project_owner_not_subscribed(self, mail, clean_mock):
        """Test JOB email is not sent to warn project owner as not subscribed."""
        # Mock for the send method
        send_mock = MagicMock()
        send_mock.send.return_value = True
        # Mock for the connection method
        connection = MagicMock()
        connection.__enter__.return_value = send_mock
        # Join them
        mail.connect.return_value = connection

        date = '2010-10-22T11:02:00.000000'
        owner = UserFactory.create(consent=True, subscribed=False)
        project = ProjectFactory.create(updated=date, owner=owner)
        project_id = project.id
        warn_old_project_owners()
        project = project_repo.get(project_id)
        err_msg = "mail.connect() should be called"
        assert mail.connect.called, err_msg
        err_msg = "conn.send() should not be called"
        assert send_mock.send.called is False, err_msg
        err_msg = "project.contacted field should be False"
        assert project.contacted is False, err_msg
        err_msg = "project.published field should be True"
        assert project.published is True, err_msg
        err_msg = "The update date should be different"
        assert project.updated == date, err_msg

    @with_context
    @patch('pybossa.cache.projects.clean')
    @patch('pybossa.core.mail')
    def test_warn_project_owner_not_consent(self, mail, clean_mock):
        """Test JOB email is not sent to warn project owner as not consent."""
        # Mock for the send method
        send_mock = MagicMock()
        send_mock.send.return_value = True
        # Mock for the connection method
        connection = MagicMock()
        connection.__enter__.return_value = send_mock
        # Join them
        mail.connect.return_value = connection

        date = '2010-10-22T11:02:00.000000'
        owner = UserFactory.create(consent=False, subscribed=True)
        project = ProjectFactory.create(updated=date, owner=owner)
        project_id = project.id
        warn_old_project_owners()
        project = project_repo.get(project_id)
        err_msg = "mail.connect() should be called"
        assert mail.connect.called, err_msg
        err_msg = "conn.send() should not be called"
        assert send_mock.send.called is False, err_msg
        err_msg = "project.contacted field should be False"
        assert project.contacted is False, err_msg
        err_msg = "project.published field should be True"
        assert project.published is True, err_msg
        err_msg = "The update date should be different"
        assert project.updated == date, err_msg

    @with_context
    @patch('pybossa.cache.projects.clean')
    def test_warn_project_owner_two(self, clean_mock):
        """Test JOB email is sent to warn project owner."""
        from pybossa.core import mail
        with mail.record_messages() as outbox:
            date = '2010-10-22T11:02:00.000000'
            owner = UserFactory.create(consent=True, subscribed=True)
            project = ProjectFactory.create(updated=date, owner=owner)
            project_id = project.id
            warn_old_project_owners()
            project = project_repo.get(project_id)
            assert len(outbox) == 1, outbox
            subject = 'Your PYBOSSA project: %s has been inactive' % project.name
            assert outbox[0].subject == subject
            err_msg = "project.contacted field should be True"
            assert project.contacted, err_msg
            err_msg = "project.published field should be False"
            assert project.published is False, err_msg
            err_msg = "cache of project should be cleaned"
            clean_mock.assert_called_with(project_id), err_msg
            err_msg = "The update date should be different"
            assert project.updated != date, err_msg

    @with_context
    @patch('pybossa.cache.projects.clean')
    def test_warn_project_excludes_completed_projects(self, clean_mock):
        """Test JOB email excludes completed projects."""
        from pybossa.core import mail
        with mail.record_messages() as outbox:
            date = '2010-10-22T11:02:00.000000'

            owner = UserFactory.create(consent=True, subscribed=True)
            project = ProjectFactory.create(updated=date, contacted=False,
                                            owner=owner)
            TaskFactory.create(created=date, project=project, state='completed')
            project_id = project.id
            project = project_repo.get(project_id)
            project.updated = date
            project_repo.update(project)

            project = ProjectFactory.create(updated=date, contacted=False,
                                            owner=owner)
            TaskFactory.create(created=date, project=project, state='ongoing')
            project_id = project.id
            project = project_repo.get(project_id)
            project.updated = date
            project_repo.update(project)

            warn_old_project_owners()
            assert len(outbox) == 1, outbox
            subject = 'Your PYBOSSA project: %s has been inactive' % project.name
            assert outbox[0].subject == subject
            err_msg = "project.contacted field should be True"
            assert project.contacted, err_msg
            err_msg = "project.published field should be False"
            assert project.published is False, err_msg
            err_msg = "cache of project should be cleaned"
            clean_mock.assert_called_with(project_id), err_msg
            err_msg = "The update date should be different"
            assert project.updated != date, err_msg
