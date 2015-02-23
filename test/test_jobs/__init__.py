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
from pybossa.jobs import create_dict_jobs, schedule_priority_jobs
from default import Test, with_context
from mock import patch

def jobs():
    """Generator."""
    return [fake_job()]

def fake_job():
    yield dict(name='name', args=[], kwargs={}, timeout=10, queue='low')


class TestJobs(Test):


    @with_context
    def test_create_dict_jobs(self):
        """Test JOB create_dict_jobs works."""
        data = [{'id': 1, 'short_name': 'app'}]
        jobs_gen = create_dict_jobs(data, 'function')
        jobs = []
        for j in jobs_gen:
            jobs.append(j)
        assert len(jobs) == 1
        assert jobs[0]['name'] == 'function'

    @with_context
    @patch('pybossa.jobs.get_scheduled_jobs')
    def test_schedule_priority_jobs_same_queue_name(self, get_scheduled_jobs):
        """Test JOB schedule_priority_jobs same queue works."""
        get_scheduled_jobs.return_value = self.jobs()
        queue_name = 'low'
        res = schedule_priority_jobs(queue_name, 10)
        msg = "%s jobs in %s have been enqueued" % (len(self.jobs), queue_name)
        assert res == msg, res

    @with_context
    @patch('pybossa.jobs.get_scheduled_jobs')
    def test_schedule_priority_jobs_diff_queue_name(self, mock_get_scheduled_jobs):
        """Test JOB schedule_priority_jobs diff queue name works."""
        mock_get_scheduled_jobs.return_value = jobs()
        queue_name = 'high'
        res = schedule_priority_jobs(queue_name, 10)
        msg = "%s jobs in %s have been enqueued" % (0, queue_name)
        assert res == msg, res
