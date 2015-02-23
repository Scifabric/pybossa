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

from pybossa.jobs import get_inactive_users_jobs, get_non_contributors_users_jobs
from default import Test, with_context
from factories import TaskRunFactory, UserFactory
from pybossa.core import user_repo
# from mock import patch, MagicMock


class TestEngageUsers(Test):

    @with_context
    def test_get_inactive_users_jobs_no_users(self):
        """Test JOB get without users returns empty list."""
        jobs_generator = get_inactive_users_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)
        msg = "There should not be any job."
        assert len(jobs) == 0,  msg

    @with_context
    def test_get_inactive_users_jobs_with_users(self):
        """Test JOB get with users returns empty list."""
        TaskRunFactory.create()
        jobs_generator = get_inactive_users_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should not be any job."
        assert len(jobs) == 0,  msg

    @with_context
    def test_get_inactive_users_returns_jobs(self):
        """Test JOB get inactive users returns a list of jobs."""

        tr = TaskRunFactory.create(finish_time="2010-07-07T17:23:45.714210")
        user = user_repo.get(tr.user_id)

        jobs_generator = get_inactive_users_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be one job."
        assert len(jobs) == 1,  msg
        job = jobs[0]
        args = job['args'][0]
        assert job['queue'] == 'quaterly', job['queue']
        assert len(args['recipients']) == 1
        assert args['recipients'][0] == user.email_addr, args['recipients'][0]
        assert "UNSUBSCRIBE" in args['body']
        assert "Update" in args['html']

    @with_context
    def test_get_inactive_users_returns_jobs_unsubscribed(self):
        """Test JOB get inactive users returns an empty list of jobs."""

        tr = TaskRunFactory.create(finish_time="2010-07-07T17:23:45.714210")
        user = user_repo.get(tr.user_id)
        user.subscribed = False
        user_repo.update(user)

        jobs_generator = get_inactive_users_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be zero jobs."
        assert len(jobs) == 0,  msg


class TestNonContributors(Test):

    @with_context
    def test_get_non_contrib_users_jobs_no_users(self):
        """Test JOB get without users returns empty list."""
        jobs_generator = get_non_contributors_users_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should not be any job."
        assert len(jobs) == 0,  msg

    @with_context
    def test_get_non_contrib_users_jobs_with_users(self):
        """Test JOB get with users returns empty list."""
        TaskRunFactory.create()
        user = user_repo.get(1)
        jobs_generator = get_non_contributors_users_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should not be any job."
        assert len(jobs) == 1,  msg
        job = jobs[0]
        args = job['args'][0]
        assert args['recipients'][0] == user.email_addr, args['recipients'][1]

    @with_context
    def test_get_non_contrib_users_returns_jobs(self):
        """Test JOB get non contrib users returns a list of jobs."""

        TaskRunFactory.create()
        user = user_repo.get(1)

        jobs_generator = get_non_contributors_users_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be one job."
        print jobs
        assert len(jobs) == 1,  msg
        job = jobs[0]
        args = job['args'][0]
        assert job['queue'] == 'quaterly', job['queue']
        assert len(args['recipients']) == 1
        assert args['recipients'][0] == user.email_addr, args['recipients'][0]
        assert "UNSUBSCRIBE" in args['body']
        assert "Update" in args['html']

    @with_context
    def test_get_non_contrib_users_returns_unsubscribed_jobs(self):
        """Test JOB get non contrib users returns a list of jobs."""

        TaskRunFactory.create()
        user = user_repo.get(1)
        user.subscribed = False
        user_repo.update(user)

        jobs_generator = get_non_contributors_users_jobs()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be zero jobs."
        assert len(jobs) == 0,  msg
