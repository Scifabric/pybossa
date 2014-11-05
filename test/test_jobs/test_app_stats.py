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

from pybossa.model.app import App
from pybossa.jobs import get_project_jobs
from default import Test, with_context
from factories import AppFactory
from factories import UserFactory
from redis import Redis
from rq_scheduler import Scheduler
from mock import patch, MagicMock


class TestProjectsStats(Test):

    def setUp(self):
        super(TestProjectsStats, self).setUp()
        self.connection = Redis()
        self.connection.flushall()
        self.scheduler = Scheduler('test_queue', connection=self.connection)

    @with_context
    def test_get_project_jobs(self):
        """Test JOB get project jobs works."""
        user = UserFactory.create(pro=True)
        app = AppFactory.create(owner=user)
        jobs = get_project_jobs()
        err_msg = "There should be only one job"

        assert len(jobs) == 1, err_msg

        job = jobs[0]
        err_msg = "There should have the same name, but it's: %s" % job['name']
        assert "get_app_stats" == job['name'].__name__, err_msg
        err_msg = "There should have the same args, but it's: %s" % job['args']
        assert [app.id, app.short_name] == job['args'], err_msg
        err_msg = "There should have the same kwargs, but it's: %s" % job['kwargs']
        assert {} == job['kwargs'], err_msg

    @with_context
    def test_get_project_jobs_for_non_pro_users(self):
        """Test JOB get project jobs works for non pro users."""
        AppFactory.create()
        jobs = get_project_jobs()

        err_msg = "There should be only 0 jobs"
        assert len(jobs) == 0, err_msg
