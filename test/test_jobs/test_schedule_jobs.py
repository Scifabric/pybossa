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

from pybossa.jobs import schedule_job
from rq_scheduler import Scheduler
import settings_test
from redis.sentinel import Sentinel


def a_function():
    return


def another_function():
    return

a_job = dict(name=a_function, args=[], kwargs={},
             interval=1, timeout=180)
another_job = dict(name=another_function, args=[], kwargs={},
                   interval=1, timeout=180)


class TestSetupScheduledJobs(object):
    """Tests for setup function 'schedule_job'"""

    def setUp(self):
        sentinel = Sentinel(settings_test.REDIS_SENTINEL)
        db = getattr(settings_test, 'REDIS_DB', 0)
        self.connection = sentinel.master_for('mymaster', db=db)
        self.connection.flushall()
        self.scheduler = Scheduler('test_queue', connection=self.connection)

    def test_adds_scheduled_job_with_interval(self):
        a_job['interval'] = 7
        schedule_job(a_job, self.scheduler)
        sched_jobs = self.scheduler.get_jobs()

        t = 0
        job = None
        for j in sched_jobs:
            job = j
            t += 1
        assert t == 1, sched_jobs
        assert job.meta['interval'] == 7 , job.meta
        a_job['interval'] = 1

    def test_adds_several_jobs_(self):
        schedule_job(a_job, self.scheduler)
        schedule_job(another_job, self.scheduler)
        sched_jobs = self.scheduler.get_jobs()
        job_func_names = [job.func_name for job in sched_jobs]
        module_name = 'test_jobs.test_schedule_jobs'

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(job)

        assert len(jobs) == 2, len(jobs)
        assert module_name + '.a_function' in job_func_names, job_func_names
        assert module_name + '.another_function' in job_func_names, job_func_names

    def test_does_not_add_job_if_already_added(self):
        schedule_job(a_job, self.scheduler)
        schedule_job(a_job, self.scheduler)
        sched_jobs = self.scheduler.get_jobs()

        jobs = []
        for job in sched_jobs:
            jobs.append(job)

        assert len(jobs) == 1, sched_jobs

    def test_returns_log_messages(self):
        success_message = schedule_job(a_job, self.scheduler)
        s_m = 'Scheduled a_function([], {}) to run every 1 seconds'
        assert success_message == s_m, (success_message, s_m)

        failure_message = schedule_job(a_job, self.scheduler)
        assert failure_message == 'WARNING: Job a_function([], {}) is already scheduled'

    def test_failed_attempt_to_schedule_does_not_polute_redis(self):
        schedule_job(a_job, self.scheduler)
        schedule_job(a_job, self.scheduler)
        stored_values = self.connection.keys('rq:job*')

        assert len(stored_values) == 1, len(stored_values)
