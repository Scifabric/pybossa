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
from redis import StrictRedis


def a_function():
    return
def another_function():
    return

a_job = dict(name=a_function, args=[], kwargs={},
             interval=1, timeout=180)
another_job = dict(name=another_function, args=[], kwargs={},
                   interval=1, timeout=180)


class TestSetupScheduledJobs(object):
    """Tests for setup function '_schedule_job'"""

    def setUp(self):
        self.connection = StrictRedis()
        self.connection.flushall()
        self.scheduler = Scheduler('test_queue', connection=self.connection)


    def test_adds_scheduled_job_with_interval(self):
        a_job['interval'] = 7
        _schedule_job(a_job, self.scheduler)
        sched_jobs = self.scheduler.get_jobs()

        assert len(sched_jobs) == 1, sched_jobs
        assert sched_jobs[0].meta['interval'] == 7 , sched_jobs[0].meta
        a_job['interval'] = 1


    def test_adds_several_jobs_(self):
        _schedule_job(a_job, self.scheduler)
        _schedule_job(another_job, self.scheduler)
        sched_jobs = self.scheduler.get_jobs()
        job_func_names = [job.func_name for job in sched_jobs]
        module_name = 'test_jobs.test_schedule_jobs'

        assert len(sched_jobs) == 2, sched_jobs
        assert module_name + '.a_function' in job_func_names, job_func_names
        assert module_name + '.another_function' in job_func_names, job_func_names


    def test_does_not_add_job_if_already_added(self):
        _schedule_job(a_job, self.scheduler)
        _schedule_job(a_job, self.scheduler)
        sched_jobs = self.scheduler.get_jobs()

        assert len(sched_jobs) == 1, sched_jobs


    def test_returns_log_messages(self):
        success_message = _schedule_job(a_job, self.scheduler)
        failure_message = _schedule_job(a_job, self.scheduler)

        assert success_message == 'Scheduled a_function([], {}) to run every 1 seconds'
        assert failure_message == 'WARNING: Job a_function([], {}) is already scheduled'


    def test_failed_attempt_to_schedule_does_not_polute_redis(self):
        _schedule_job(a_job, self.scheduler)
        _schedule_job(a_job, self.scheduler)
        stored_values = self.connection.keys('rq:job*')

        assert len(stored_values) == 1, len(stored_values)
