# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

from datetime import datetime
from pybossa.jobs import create_dict_jobs, enqueue_periodic_jobs,\
    get_quarterly_date, get_periodic_jobs
from mock import patch
from nose.tools import assert_raises

def jobs():
    """Generator."""
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='low')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='low')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='high')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='super')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='medium')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='monthly')
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='quaterly')


class TestJobs(object):


    def test_create_dict_jobs(self):
        """Test JOB create_dict_jobs works."""
        data = [{'id': 1, 'short_name': 'app'}]
        jobs_gen = create_dict_jobs(data, 'function')
        jobs = []
        for j in jobs_gen:
            jobs.append(j)
        assert len(jobs) == 1
        assert jobs[0]['name'] == 'function'

    @patch('pybossa.jobs.get_periodic_jobs')
    def test_enqueue_periodic_jobs(self, get_periodic_jobs):
        """Test JOB enqueue_periodic_jobs works."""
        get_periodic_jobs.return_value = jobs()
        queue_name = 'low'
        res = enqueue_periodic_jobs(queue_name)
        expected_jobs = [job for job in jobs() if job['queue'] == queue_name]
        msg = "%s jobs in %s have been enqueued" % (len(expected_jobs), queue_name)
        assert res == msg, res

    @patch('pybossa.jobs.get_periodic_jobs')
    def test_enqueue_periodic_jobs_bad_queue_name(self, mock_get_periodic_jobs):
        """Test JOB enqueue_periodic_jobs diff queue name works."""
        mock_get_periodic_jobs.return_value = jobs()
        queue_name = 'badqueue'
        res = enqueue_periodic_jobs(queue_name)
        msg = "%s jobs in %s have been enqueued" % (0, queue_name)
        assert res == msg, res

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
        assert project.called == False
        assert autoimport.called == False

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

    def test_get_quarterly_date_1st_quarter_returns_31_march(self):
        january_1st = datetime(2015, 1, 1)
        february_2nd = datetime(2015, 2, 2)
        march_31st = datetime(2015, 3, 31)

        assert get_quarterly_date(january_1st) == datetime(2015, 3, 31)
        assert get_quarterly_date(february_2nd) == datetime(2015, 3, 31)
        assert get_quarterly_date(march_31st) == datetime(2015, 3, 31)

    def test_get_quarterly_date_2nd_quarter_returns_30_june(self):
        april_1st = datetime(2015, 4, 1)
        may_5th = datetime(2015, 5, 5)
        june_30th = datetime(2015, 4, 10)

        assert get_quarterly_date(april_1st) == datetime(2015, 6, 30)
        assert get_quarterly_date(may_5th) == datetime(2015, 6, 30)
        assert get_quarterly_date(june_30th) == datetime(2015, 6, 30)

    def test_get_quarterly_date_3rd_quarter_returns_30_september(self):
        july_1st = datetime(2015, 7, 1)
        august_6th = datetime(2015, 8, 6)
        september_30th = datetime(2015, 9, 30)

        assert get_quarterly_date(july_1st) == datetime(2015, 9, 30)
        assert get_quarterly_date(august_6th) == datetime(2015, 9, 30)
        assert get_quarterly_date(september_30th) == datetime(2015, 9, 30)

    def test_get_quarterly_date_4th_quarter_returns_31_december(self):
        october_1st = datetime(2015, 10, 1)
        november_24th = datetime(2015, 11,24)
        december_31st = datetime(2015, 12, 31)

        assert get_quarterly_date(october_1st) == datetime(2015, 12, 31)
        assert get_quarterly_date(november_24th) == datetime(2015, 12, 31)
        assert get_quarterly_date(december_31st) == datetime(2015, 12, 31)

    def test_get_quarterly_date_returns_same_time_as_passed(self):
        now = datetime.utcnow()

        returned_date = get_quarterly_date(now)

        assert now.time() == returned_date.time()

    def test_get_quarterly_date_raises_TypeError_on_wrong_args(self):
        assert_raises(TypeError, get_quarterly_date, 'wrong_arg')
