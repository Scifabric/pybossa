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

from pybossa.jobs import get_inactive_users_jobs
from default import Test, with_context
from factories import TaskRunFactory
from pybossa.core import user_repo
# from mock import patch, MagicMock


class TestEngageUsers(Test):

    @with_context
    def test_get_inactive_users_jobs_no_users(self):
        """Test JOB get without users returns empty list."""
        jobs = get_inactive_users_jobs()
        msg = "There should not be any job."
        assert len(jobs) == 0,  msg

    @with_context
    def test_get_inactive_users_jobs_with_users(self):
        """Test JOB get with users returns empty list."""
        TaskRunFactory.create()
        jobs = get_inactive_users_jobs()
        msg = "There should not be any job."
        assert len(jobs) == 0,  msg

    @with_context
    def test_get_inactive_users_returns_jobs(self):
        """Test JOB get inactive users returns a list of jobs."""

        tr = TaskRunFactory.create(finish_time="2010-07-07T17:23:45.714210")
        user = user_repo.get(tr.user_id)

        jobs = get_inactive_users_jobs()
        msg = "There should not be one job."
        assert len(jobs) == 1,  msg
        job = jobs[0]
        args = job['args'][0]
        assert job['queue'] == 'quaterly', job['queue']
        assert len(args['recipients']) == 1
        assert args['recipients'][0] == user.email_addr, args['recipients'][0]


# class TestNonContributors(Test):
#
#     @with_context
#     def test_get_non_contributors_users_jobs(self):
#         """Test JOB get returns empty list."""
#         jobs = get_non_contributors_users_jobs()
#         msg = "There should not be any job."
#         assert len(jobs) == 0,  msg
#
#     @with_context
#     def test_get_inactive_users_returns_jobs(self):
#         """Test JOB get inactive users returns a list of jobs."""
#
#         tr = TaskRunFactory.create(finish_time="2010-07-07T17:23:45.714210")
#         user = user_repo.get(tr.user_id)
#
#         jobs = get_inactive_users_jobs()
#         msg = "There should not be one job."
#         assert len(jobs) == 1,  msg
#         job = jobs[0]
#         args = job['args'][0]
#         assert job['queue'] == 'quaterly', job['queue']
#         assert len(args['recipients']) == 1
#         assert args['recipients'][0] == user.email_addr, args['recipients'][0]
