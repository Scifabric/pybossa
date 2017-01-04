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
from default import Test, with_context, flask_app
from factories import ProjectFactory, UserFactory
from pybossa.jobs import get_export_task_jobs, project_export
from mock import patch

class TestExport(Test):

    @with_context
    @patch.dict(flask_app.config, {'PRO_FEATURES': {'updated_exports': True}})
    def test_get_export_task_jobs(self):
        """Test JOB export task jobs works."""
        project = ProjectFactory.create()
        jobs_generator = get_export_task_jobs(queue='low')
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be only one job."
        assert len(jobs) == 1, len(jobs)
        job = jobs[0]
        msg = "The job should be for the same project.id"
        assert job['args'] == [project.id], msg
        msg = "The job should be enqueued in low priority."
        assert job['queue'] == 'low', msg

    @with_context
    @patch.dict(flask_app.config, {'PRO_FEATURES': {'updated_exports': True}})
    def test_get_export_task_pro_jobs(self):
        """Test JOB export task jobs for pro users works."""
        user = UserFactory.create(pro=True)
        project = ProjectFactory.create(owner=user)
        jobs_generator = get_export_task_jobs(queue='high')
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be only one job."
        assert len(jobs) == 1, len(jobs)
        job = jobs[0]
        msg = "The job should be for the same project.id"
        assert job['args'] == [project.id], msg
        msg = "The job should be enqueued in high priority."
        assert job['queue'] == 'high', msg

    @with_context
    @patch.dict(flask_app.config, {'PRO_FEATURES': {'updated_exports': False}})
    def test_get_export_task_jobs_pro_disabled_high_queue(self):
        """Test JOB export task jobs returns non pro projects for high queue if
        updated exports is enabled for everyone."""
        user = UserFactory.create()
        project = ProjectFactory.create(owner=user)
        jobs_generator = get_export_task_jobs(queue='high')
        jobs = []
        for job in jobs_generator:
            jobs.append(job)

        msg = "There should be only one job."
        assert len(jobs) == 1, len(jobs)
        job = jobs[0]
        msg = "The job should be for the same project.id"
        assert job['args'] == [project.id], msg
        msg = "The job should be enqueued in high priority."
        assert job['queue'] == 'high', msg

    @with_context
    @patch('pybossa.core.json_exporter')
    @patch('pybossa.core.csv_exporter')
    def test_project_export(self, csv_exporter, json_exporter):
        """Test JOB project_export works."""
        project = ProjectFactory.create()
        project_export(project.id)
        csv_exporter.pregenerate_zip_files.assert_called_once_with(project)
        json_exporter.pregenerate_zip_files.assert_called_once_with(project)

    @with_context
    @patch('pybossa.core.json_exporter')
    @patch('pybossa.core.csv_exporter')
    def test_project_export_none(self, csv_exporter, json_exporter):
        """Test JOB project_export without project works."""
        project_export(0)
        assert not csv_exporter.pregenerate_zip_files.called
        assert not json_exporter.pregenerate_zip_files.called
