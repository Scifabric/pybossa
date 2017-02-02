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

import json
from pybossa.core import sentinel
from pybossa.jobs import check_failed
from default import Test, with_context, FakeResponse, db
from redis import StrictRedis
from mock import patch, MagicMock, call


class TestMaintenance(Test):

    def setUp(self):
        super(TestMaintenance, self).setUp()
        self.connection = StrictRedis()
        self.connection.flushall()

    @with_context
    @patch('pybossa.jobs.send_mail')
    @patch('rq.requeue_job', autospec=True)
    @patch('rq.get_failed_queue', autospec=True)
    def test_check_failed(self, mock_failed_queue, mock_requeue_job, mock_send_mail):
        """Test JOB check failed works."""
        #mock_failed_queue = MagicMock()
        fq = MagicMock
        fq.job_ids = ['1']
        job = MagicMock()
        fq.fetch_job = job
        mock_failed_queue.return_value = fq
        for i in range(self.flask_app.config.get('FAILED_JOBS_RETRIES')):
            response = check_failed()
            msg = "JOBS: ['1'] You have failed the system."
            assert msg == response, response
            mock_requeue_job.assert_called_with('1')
        response = check_failed()
        assert mock_send_mail.called
        mock_send_mail.reset_mock()
        response = check_failed()
        assert not mock_send_mail.called
