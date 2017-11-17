# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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


from pybossa.jobs import mail_project_report
from mock import patch
from default import Fixtures, with_context
from helper import web
from helper.gig_helper import make_subadmin_by


@with_context
@patch('pybossa.jobs.send_mail')
def test_report(mail):
    Fixtures.create_project({})
    info = {
        'timestamp': 'timestamp',
        'user_id': 42,
        'base_url': 'www.example.com/project/'
    }
    mail_project_report(info, 'tyrion@casterlyrock.com')
    args, _ = mail.call_args
    message = args[0]
    assert 'tyrion@casterlyrock.com' in message.recipients
    assert 'Your exported data is attached.' in message.body, message.body
    assert message.attachments, 'no data was attached'


@with_context
@patch('pybossa.jobs.send_mail')
@patch('pybossa.core.project_csv_exporter')
def test_report_fails(exporter, mail):
    Fixtures.create_project({})
    exporter.pregenerate_zip_files.side_effect = Exception()
    info = {
        'timestamp': 'timestamp',
        'user_id': 42,
        'base_url': 'www.example.com/project/'
    }
    mail_project_report(info, 'tyrion@casterlyrock.com')
    args, _ = mail.call_args
    message = args[0]
    assert 'tyrion@casterlyrock.com' in message.recipients
    assert 'An error occurred while exporting your report.' in message.body, message.body


class TestAllProjectsReport(web.Helper):

    @with_context
    def test_request_report(self):
        """Test WEB home page works"""
        self.register()
        self.signin()
        self.create_categories()

        res = self.app.get('/project/export',
                           follow_redirects=True)

        assert 'You will be emailed when your export has been completed' in res.data, res.data

    @with_context
    def test_non_admin_request_report(self):
        """Test WEB home page works"""
        self.register()
        self.signin()
        self.create_categories()
        self.register(name='tyrion')
        self.signout()
        self.signin(email='tyrion@example.com')

        # user can't access report
        res = self.app.get('/project/export?format=csv',
                           follow_redirects=True)
        assert res.status_code == 403, res.status

        # subadmin can't access report
        make_subadmin_by(email_addr='tyrion@example.com')
        res = self.app.get('/project/export?format=csv',
                           follow_redirects=True)
        assert res.status_code == 403, res.status
