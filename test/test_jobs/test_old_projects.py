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

from pybossa.jobs import warn_old_project_owners, get_non_updated_projects
from default import Test, with_context
from factories import ProjectFactory
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
    @patch('pybossa.core.mail')
    def test_warn_project_owner(self, mail):
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
        project = ProjectFactory.create(updated=date)
        project_id = project.id
        warn_old_project_owners()
        err_msg = "mail.connect() should be called"
        assert mail.connect.called, err_msg
        err_msg = "conn.send() should be called"
        assert send_mock.send.called, err_msg
        err_msg = "project.contacted field should be True"
        assert project.contacted, err_msg
        err_msg = "The update date should be different"
        assert project.updated != date, err_msg

    @with_context
    def test_warn_project_owner_two(self):
        """Test JOB email is sent to warn project owner."""
        from pybossa.core import mail
        with mail.record_messages() as outbox:
            date = '2010-10-22T11:02:00.000000'
            project = ProjectFactory.create(updated=date)
            project_id = project.id
            warn_old_project_owners()
            assert len(outbox) == 1, outbox
            subject = 'Your PyBossa project: %s has been inactive' % project.name
            assert outbox[0].subject == subject
            err_msg = "project.contacted field should be True"
            assert project.contacted, err_msg
            err_msg = "The update date should be different"
            assert project.updated != date, err_msg

    @with_context
    def test_warn_project_owner_limits(self):
        """Test JOB email gets at most 25 projects."""
        from pybossa.core import mail
        # Create 50 projects with old updated dates
        date = '2010-10-22T11:02:00.000000'
        projects = []
        for i in range(0, 50):
            projects.append(ProjectFactory.create(updated=date))
        # The first day that we run the job only 25 emails should be sent
        with mail.record_messages() as outbox:
            warn_old_project_owners()
            err_msg = "There should be only 25 emails."
            assert len(outbox) == 25, err_msg
        # The second day that we run the job only 25 emails should be sent
        with mail.record_messages() as outbox:
            warn_old_project_owners()
            err_msg = ("There should be only 25 emails, but there are %s."
                       % len(outbox))
            assert len(outbox) == 25, err_msg
        # The third day that we run the job only 0 emails should be sent
        # as the previous projects have been already contacted.
        with mail.record_messages() as outbox:
            warn_old_project_owners()
            err_msg = "There should be only 0 emails."
            assert len(outbox) == 0, err_msg
