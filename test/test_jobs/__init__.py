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

from pybossa.core import _schedule_job
from rq_scheduler import Scheduler
from redis import Redis


def a_function():
    return
def another_function():
    return


class TestSetupScheduledJobs(object):
    """Tests for setup function '_schedule_jobs'"""

    def setUp(self):
        self.connection = Redis()
        self.connection.flushall()
        self.scheduler = Scheduler('test_queue', connection=self.connection)


    def test_adds_scheduled_job_with_interval(self):
        interval = 7
        _schedule_job(a_function, interval, self.scheduler)
        sched_jobs = self.scheduler.get_jobs()

        assert len(sched_jobs) == 1, sched_jobs
        assert sched_jobs[0].meta['interval'] == interval, sched_jobs[0].meta


    def test_adds_several_jobs_(self):
        _schedule_job(a_function, 1, self.scheduler)
        _schedule_job(another_function, 1, self.scheduler)
        sched_jobs = self.scheduler.get_jobs()
        job_func_names = [job.func_name for job in sched_jobs]

        assert len(sched_jobs) == 2, sched_jobs
        assert 'test_jobs.a_function' in job_func_names, job_func_names
        assert 'test_jobs.another_function' in job_func_names


    def test_does_not_add_job_if_already_added(self):
        _schedule_job(a_function, 1, self.scheduler)
        _schedule_job(a_function, 1, self.scheduler)
        sched_jobs = self.scheduler.get_jobs()

        assert len(sched_jobs) == 1, sched_jobs


    def test_returns_log_messages(self):
        success_message = _schedule_job(a_function, 1, self.scheduler)
        failure_message = _schedule_job(a_function, 1, self.scheduler)

        assert success_message == 'Scheduled a_function to run every 1 seconds'
        assert failure_message == 'Job a_function is already scheduled'


    def test_failed_attempt_to_schedule_does_not_polute_redis(self):
        _schedule_job(a_function, 1, self.scheduler)
        _schedule_job(a_function, 1, self.scheduler)
        stored_values = self.connection.keys('rq:job*')

        assert len(stored_values) == 1, len(stored_values)
