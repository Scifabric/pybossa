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

from datetime import datetime
from pybossa.jobs import create_dict_jobs, enqueue_periodic_jobs,\
    get_quarterly_date, get_periodic_jobs, delete_account
from pybossa.core import user_repo, task_repo, db
from mock import patch
from nose.tools import assert_raises
from default import with_context, Test
from factories import TaskRunFactory, UserFactory, ProjectFactory
from dateutil.relativedelta import relativedelta

def jobs():
    """Generator."""
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='email')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='low')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='low')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='high')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='super')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='medium')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='monthly')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='bimonthly')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='quaterly')


class TestJobs(Test):


    @with_context
    def test_create_dict_jobs(self):
        """Test JOB create_dict_jobs works."""
        data = [{'id': 1, 'short_name': 'app'}]
        timeout = self.flask_app.config.get('TIMEOUT')
        jobs_gen = create_dict_jobs(data, 'function', timeout)
        jobs = []
        for j in jobs_gen:
            jobs.append(j)
        assert len(jobs) == 1
        assert jobs[0]['name'] == 'function', jobs[0]
        assert jobs[0]['timeout'] == timeout, jobs[0]

    @with_context
    def test_get_default_jobs(self):
        """Test JOB get_default_jobs works."""
        from pybossa.jobs import warm_up_stats, warn_old_project_owners
        from pybossa.jobs import warm_cache, news, get_default_jobs
        timeout = self.flask_app.config.get('TIMEOUT')
        job_names = [warm_up_stats, warn_old_project_owners, warm_cache, news]
        for job in get_default_jobs():
            assert job['timeout'] == timeout, job
            assert job['name'] in job_names, job

    @with_context
    @patch('pybossa.jobs.get_periodic_jobs')
    def test_enqueue_periodic_jobs(self, get_periodic_jobs):
        """Test JOB enqueue_periodic_jobs works."""
        get_periodic_jobs.return_value = jobs()
        queue_name = 'low'
        res = enqueue_periodic_jobs(queue_name)
        expected_jobs = [job for job in jobs() if job['queue'] == queue_name]
        msg = "%s jobs in %s have been enqueued" % (len(expected_jobs), queue_name)
        assert res == msg, res

    @with_context
    @patch('pybossa.jobs.get_periodic_jobs')
    def test_enqueue_periodic_jobs_bad_queue_name(self, mock_get_periodic_jobs):
        """Test JOB enqueue_periodic_jobs diff queue name works."""
        mock_get_periodic_jobs.return_value = jobs()
        queue_name = 'badqueue'
        res = enqueue_periodic_jobs(queue_name)
        msg = "%s jobs in %s have been enqueued" % (0, queue_name)
        assert res == msg, res

    @with_context
    @patch('pybossa.jobs.get_export_task_jobs')
    @patch('pybossa.jobs.get_project_jobs')
    @patch('pybossa.jobs.get_autoimport_jobs')
    @patch('pybossa.jobs.get_inactive_users_jobs')
    @patch('pybossa.jobs.get_non_contributors_users_jobs')
    def test_get_periodic_jobs_with_low_queue(self, non_contr, inactive,
            autoimport, project, export):
        export.return_value = jobs()
        autoimport.return_value = jobs()
        low_jobs = get_periodic_jobs('low')
        # Only returns jobs for the specified queue
        for job in low_jobs:
            assert job['queue'] == 'low'
        # Does not call unnecessary functions for performance
        assert non_contr.called == False
        assert inactive.called == False
        assert project.called == False

    @with_context
    @patch('pybossa.jobs.get_export_task_jobs')
    @patch('pybossa.jobs.get_project_jobs')
    @patch('pybossa.jobs.get_autoimport_jobs')
    @patch('pybossa.jobs.get_inactive_users_jobs')
    @patch('pybossa.jobs.get_non_contributors_users_jobs')
    def test_get_periodic_jobs_with_high_queue(self, non_contr, inactive,
            autoimport, project, export):
        export.return_value = jobs()
        high_jobs = get_periodic_jobs('high')
        # Only returns jobs for the specified queue
        for job in high_jobs:
            assert job['queue'] == 'high'
        # Does not call unnecessary functions for performance
        assert non_contr.called == False
        assert inactive.called == False
        assert project.called == True
        assert autoimport.called == False

    @with_context
    @patch('pybossa.jobs.get_export_task_jobs')
    @patch('pybossa.jobs.get_project_jobs')
    @patch('pybossa.jobs.get_autoimport_jobs')
    @patch('pybossa.jobs.get_inactive_users_jobs')
    @patch('pybossa.jobs.get_non_contributors_users_jobs')
    def test_get_periodic_jobs_with_super_queue(self, non_contr, inactive,
            autoimport, project, export):
        project.return_value = jobs()
        super_jobs = get_periodic_jobs('super')
        # Only returns jobs for the specified queue
        for job in super_jobs:
            assert job['queue'] == 'super'
        # Does not call unnecessary functions for performance
        assert non_contr.called == False
        assert inactive.called == False
        assert export.called == False
        assert autoimport.called == False

    @with_context
    @patch('pybossa.jobs.get_export_task_jobs')
    @patch('pybossa.jobs.get_project_jobs')
    @patch('pybossa.jobs.get_autoimport_jobs')
    @patch('pybossa.jobs.get_inactive_users_jobs')
    @patch('pybossa.jobs.get_non_contributors_users_jobs')
    def test_get_periodic_jobs_with_quaterly_queue(self, non_contr, inactive,
            autoimport, project, export):
        inactive.return_value = jobs()
        non_contr.return_value = jobs()
        quaterly_jobs = get_periodic_jobs('quaterly')
        # Only returns jobs for the specified queue
        for job in quaterly_jobs:
            assert job['queue'] == 'quaterly'
        # Does not call unnecessary functions for performance
        assert autoimport.called == False
        assert export.called == False
        assert project.called == False

    @with_context
    def test_get_quarterly_date_1st_quarter_returns_31_march(self):
        january_1st = datetime(2015, 1, 1)
        february_2nd = datetime(2015, 2, 2)
        march_31st = datetime(2015, 3, 31)

        assert get_quarterly_date(january_1st) == datetime(2015, 3, 31)
        assert get_quarterly_date(february_2nd) == datetime(2015, 3, 31)
        assert get_quarterly_date(march_31st) == datetime(2015, 3, 31)

    @with_context
    def test_get_quarterly_date_2nd_quarter_returns_30_june(self):
        april_1st = datetime(2015, 4, 1)
        may_5th = datetime(2015, 5, 5)
        june_30th = datetime(2015, 4, 10)

        assert get_quarterly_date(april_1st) == datetime(2015, 6, 30)
        assert get_quarterly_date(may_5th) == datetime(2015, 6, 30)
        assert get_quarterly_date(june_30th) == datetime(2015, 6, 30)

    @with_context
    def test_get_quarterly_date_3rd_quarter_returns_30_september(self):
        july_1st = datetime(2015, 7, 1)
        august_6th = datetime(2015, 8, 6)
        september_30th = datetime(2015, 9, 30)

        assert get_quarterly_date(july_1st) == datetime(2015, 9, 30)
        assert get_quarterly_date(august_6th) == datetime(2015, 9, 30)
        assert get_quarterly_date(september_30th) == datetime(2015, 9, 30)

    @with_context
    def test_get_quarterly_date_4th_quarter_returns_31_december(self):
        october_1st = datetime(2015, 10, 1)
        november_24th = datetime(2015, 11,24)
        december_31st = datetime(2015, 12, 31)

        assert get_quarterly_date(october_1st) == datetime(2015, 12, 31)
        assert get_quarterly_date(november_24th) == datetime(2015, 12, 31)
        assert get_quarterly_date(december_31st) == datetime(2015, 12, 31)

    @with_context
    def test_get_quarterly_date_returns_same_time_as_passed(self):
        now = datetime.utcnow()

        returned_date = get_quarterly_date(now)

        assert now.time() == returned_date.time()

    @with_context
    def test_get_quarterly_date_raises_TypeError_on_wrong_args(self):
        assert_raises(TypeError, get_quarterly_date, 'wrong_arg')

    @with_context
    def test_get_periodic_jobs_with_monthly_queue(self):
        # create root user
        UserFactory.create()
        projectOwner = UserFactory.create(admin=False)
        ProjectFactory.create(owner=projectOwner)
        today = datetime.today()
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

        jobs = get_periodic_jobs('monthly')
        # Only returns jobs for the specified queue
        for job in jobs:
            assert job['queue'] == 'monthly'
            assert 'delete' in job['args'][0]['subject'], job['args']
            assert [tr_year.user.email_addr] == job['args'][0]['recipients'], job['args']

    @with_context
    def test_get_periodic_jobs_with_bimonthly_queue(self):
        # create root user
        UserFactory.create()
        projectOwner = UserFactory.create(admin=False)
        ProjectFactory.create(owner=projectOwner)
        today = datetime.today()
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

        jobs = get_periodic_jobs('bimonthly')
        # Only returns jobs for the specified queue
        for job in jobs:
            assert job['queue'] == 'bimonthly'
            assert job['name'] == delete_account
            assert tr_year.user.id == job['args'][0], (tr_year.user.id,
                                                         job['args'])
