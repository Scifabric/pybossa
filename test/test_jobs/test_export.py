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
from default import Test, with_context
from factories import AppFactory, UserFactory
from pybossa.jobs import get_export_task_jobs, project_export
from mock import patch

class TestExport(Test):

    @with_context
    def test_get_export_task_jobs(self):
        """Test JOB export task jobs works."""
        app = AppFactory.create()
        jobs = get_export_task_jobs()
        msg = "There should be only one job."
        assert len(jobs) == 1, len(jobs)
        job = jobs[0]
        msg = "The job should be for the same app.id"
        assert job['args'] == [app.id], msg
        msg = "The job should be enqueued in low priority."
        assert job['queue'] == 'low', msg

    @with_context
    def test_get_export_task_pro_jobs(self):
        """Test JOB export task jobs for pro users works."""
        user = UserFactory.create(pro=True)
        app = AppFactory.create(owner=user)
        jobs = get_export_task_jobs()
        msg = "There should be only one job."
        assert len(jobs) == 1, len(jobs)
        job = jobs[0]
        msg = "The job should be for the same app.id"
        assert job['args'] == [app.id], msg
        msg = "The job should be enqueued in high priority."
        assert job['queue'] == 'high', msg

    @with_context
    @patch('pybossa.core.json_exporter')
    @patch('pybossa.core.csv_exporter')
    def test_project_export(self, csv_exporter, json_exporter):
        """Test JOB project_export works."""
        app = AppFactory.create()
        project_export(app.id)
        csv_exporter.pregenerate_zip_files.assert_called_once_with(app)
        json_exporter.pregenerate_zip_files.assert_called_once_with(app)

    @with_context
    @patch('pybossa.core.json_exporter')
    @patch('pybossa.core.csv_exporter')
    def test_project_export_none(self, csv_exporter, json_exporter):
        """Test JOB project_export without project works."""
        project_export(0)
        assert not csv_exporter.pregenerate_zip_files.called
        assert not json_exporter.pregenerate_zip_files.called
