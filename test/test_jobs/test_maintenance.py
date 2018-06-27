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

from pybossa.core import sentinel
from pybossa.jobs import check_failed, get_maintenance_jobs
from default import Test, with_context, FakeResponse, db
from mock import patch, MagicMock


class TestMaintenance(Test):

    def setUp(self):
        super(TestMaintenance, self).setUp()
        self.connection = sentinel.master
        self.connection.flushall()

    @with_context
    def test_get_maintenance_jobs(self):
        """Test get maintenance jobs works."""
        res = next(get_maintenance_jobs())
        assert res['queue'] == 'maintenance'

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('rq.requeue_job', autospec=True)
    @patch('rq.get_failed_queue', autospec=True)
    def test_check_failed_variant(self, mock_failed_queue, mock_requeue_job, mock_send_mail):
        """Test JOB check failed works when no failed jobs."""
        fq = MagicMock
        fq.job_ids = []
        job = MagicMock()
        fq.fetch_job = job
        mock_failed_queue.return_value = fq
        response = check_failed()
        msg = "You have not failed the system"
        assert msg == response, response

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('rq.requeue_job', autospec=True)
    @patch('rq.get_failed_queue', autospec=True)
    def test_check_failed(self, mock_failed_queue, mock_requeue_job, mock_send_mail):
        """Test JOB check failed works."""
        fq = MagicMock
        fq.job_ids = ['1']
        job = MagicMock()
        fq.fetch_job = job
        mock_failed_queue.return_value = fq
        for i in range(self.flask_app.config.get('FAILED_JOBS_RETRIES') - 1):
            response = check_failed()
            msg = "JOBS: ['1'] You have failed the system."
            assert msg == response, response
            mock_requeue_job.assert_called_with('1')
            assert not mock_send_mail.called
        response = check_failed()
        assert mock_send_mail.called
        mock_send_mail.reset_mock()
        response = check_failed()
        assert not mock_send_mail.called
