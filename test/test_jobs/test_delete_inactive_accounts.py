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

import dateutil.relativedelta
from pybossa.jobs import get_delete_inactive_accounts
from pybossa.jobs import get_notify_inactive_accounts
from default import Test, with_context, rebuild_db
from factories import TaskRunFactory, UserFactory, ProjectFactory
from pybossa.core import user_repo, task_repo, db
from pybossa.model.task_run import TaskRun
from pybossa.model.user import User
import datetime
from dateutil.relativedelta import relativedelta
import calendar


class TestEngageUsers(Test):

    @with_context
    def test_get_notify_no_users(self):
        """Test JOB get without users returns empty list."""
        jobs_generator = get_notify_inactive_accounts()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)
        msg = "There should not be any job."
        assert len(jobs) == 0,  msg

    @with_context
    def test_get_notify_with_users(self):
        """Test JOB get with users returns empty list."""
        user = UserFactory.create()
        tr = TaskRunFactory.create(user=user)
        jobs_generator = get_notify_inactive_accounts()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)
        msg = "There should not be any job."
        assert len(jobs) == 0,  msg

    @with_context
    def test_get_notify_returns_jobs(self):
        """Test JOB get inactive users returns a list of jobs."""
        # create root user
        UserFactory.create()
        projectOwner = UserFactory.create(admin=False)
        ProjectFactory.create(owner=projectOwner)
        today = datetime.datetime.today()
        old_date = today + relativedelta(months=-1)
        date_str = old_date.strftime('%Y-%m-%dT%H:%M:%S.%f')
        # substract six months and take care of leap years
        one_year = today + relativedelta(months=-6, leapdays=1)
        one_year_str = one_year.strftime('%Y-%m-%dT%H:%M:%S.%f')
        user = UserFactory.create()
        user_recent = UserFactory.create()
        # 1 month old contribution
        tr = TaskRunFactory.create(finish_time=date_str)
        # 1 year old contribution
        tr_year = TaskRunFactory.create(finish_time=one_year_str)
        # 1 year old contribution for a project owner
        tr_year_project = TaskRunFactory.create(finish_time=one_year_str,
                                                user=projectOwner)
        # User with a contribution from a long time ago
        tr2 = TaskRunFactory.create(finish_time="2010-08-08T18:23:45.714110",
                                    user=user)
        # User with a recent contribution
        tr3 = TaskRunFactory.create(user=user)
        user = user_repo.get(tr.user_id)

        jobs_generator = get_notify_inactive_accounts()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be one job."
        assert len(jobs) == 1, (msg, len(jobs))
        emails = [tr_year.user.email_addr]
        for job in jobs:
            args = job['args'][0]
            email = args['recipients'][0]
            assert email in emails, (email, emails)
            job['name'](*job['args'])
        job = jobs[0]
        args = job['args'][0]
        assert job['queue'] == 'monthly', job['queue']
        assert len(args['recipients']) == 1
        assert args['recipients'][0] == tr_year.user.email_addr, args['recipients'][0]
        assert "deleted the next month" in args['subject']
        user = User.query.get(tr_year.user.id)
        assert tr_year.user.notified_at is not None, jobs
        assert tr_year.user.notified_at.strftime('%Y-%m-%d') == today.strftime('%Y-%m-%d')

    @with_context
    def test_delete_jobs(self):
        """Test JOB returns jobs to delete inactive accounts."""
        # create root user
        UserFactory.create()
        projectOwner = UserFactory.create(admin=False)
        ProjectFactory.create(owner=projectOwner)
        today = datetime.datetime.today()
        old_date = today + relativedelta(months=-1)
        date_str = old_date.strftime('%Y-%m-%dT%H:%M:%S.%f')
        # substract six months and take care of leap years
        one_year = today + relativedelta(months=-6, leapdays=1)
        one_year_str = one_year.strftime('%Y-%m-%dT%H:%M:%S.%f')
        user = UserFactory.create()
        user_recent = UserFactory.create()
        # 1 month old contribution
        tr = TaskRunFactory.create(finish_time=date_str)
        # 1 year old contribution
        tr_year = TaskRunFactory.create(finish_time=one_year_str)
        # 1 year old contribution for a project owner
        tr_year_project = TaskRunFactory.create(finish_time=one_year_str,
                                                user=projectOwner)
        # User with a contribution from a long time ago
        tr2 = TaskRunFactory.create(finish_time="2010-08-08T18:23:45.714110",
                                    user=user)
        # User with a recent contribution
        tr3 = TaskRunFactory.create(user=user)
        user = user_repo.get(tr.user_id)

        jobs = []
        jobs_generator = get_notify_inactive_accounts()
        for job in jobs_generator:
            jobs.append(job)
            job['name'](*job['args'])
        msg = "There should be one job."
        assert len(jobs) == 1, (msg, len(jobs))

        # The user will get today (the day that the tests are run) as their notified_at value
        # We need to change it to one month ago, to trigger the delete action
        assert tr_year.user.notified_at is not None, jobs
        assert tr_year.user.notified_at.strftime('%Y-%m-%d') == today.strftime('%Y-%m-%d')

        one_month_ago = today - dateutil.relativedelta.relativedelta(months=1)
        tr_year.user.notified_at = one_month_ago
        db.session.add(tr_year.user)
        db.session.commit()

        assert tr_year.user.notified_at.strftime('%Y-%m-%d') == one_month_ago.strftime('%Y-%m-%d')

        jobs_generator = get_delete_inactive_accounts()
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be one job."
        assert len(jobs) == 1, (msg, len(jobs))
        emails = [tr_year.user.id]
        for job in jobs:
            err_msg = "Delete user is not the same"
            assert job['args'][0] == tr_year.user.id, err_msg
        job = jobs[0]
        args = job['args'][0]
        assert job['queue'] == 'bimonthly', job['queue']
