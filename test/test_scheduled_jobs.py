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

from pybossa.core import _schedule_job

from rq_scheduler import Scheduler
from mock import patch, MagicMock
from redis import Redis


class TestSetupScheduledJobs(object):
    """Unit tests for setup function '_schedule_jobs'"""

    def setUp(self):
        self.connection = Redis()
        self.connection.flushall()


    def test_adds_scheduled_job_with_interval(self):
        scheduler = Scheduler('test_queue', connection=self.connection)
        def a_function():
            return
        interval = 7
        _schedule_job(a_function, interval, scheduler)
        sched_jobs = scheduler.get_jobs()

        assert len(sched_jobs) == 1, sched_jobs
        assert sched_jobs[0].meta['interval'] == interval, sched_jobs[0].meta


    def test_adds_several_jobs_(self):
        scheduler = Scheduler('test_queue', connection=self.connection)
        def a_function():
            return
        def another_function():
            return

        _schedule_job(a_function, 1, scheduler)
        _schedule_job(another_function, 1, scheduler)
        sched_jobs = scheduler.get_jobs()
        job_func_names = [job.func_name for job in sched_jobs]

        assert len(sched_jobs) == 2, sched_jobs
        assert 'test_scheduled_jobs.a_function' in job_func_names
        assert 'test_scheduled_jobs.another_function' in job_func_names


    def test_does_not_add_job_if_already_added(self):
        scheduler = Scheduler('test_queue', connection=self.connection)
        def a_function():
            return

        _schedule_job(a_function, 1, scheduler)
        _schedule_job(a_function, 1, scheduler)
        sched_jobs = scheduler.get_jobs()

        assert len(sched_jobs) == 1, sched_jobs
