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

from default import with_context
from pybossa.jobs import send_mail
from mock import patch


class TestSendMailJob(object):

    @with_context
    @patch('pybossa.jobs.mail')
    @patch('pybossa.jobs.Message')
    def test_send_mail_craetes_message(self, Message, mail):
        mail_dict = dict(subject='Hello', recipients=['pepito@hotmail.con'],
                         body='Hello Pepito!')
        send_mail(mail_dict)
        Message.assert_called_once_with(**mail_dict)
        assert mail.send.called

    @with_context
    @patch('pybossa.jobs.mail')
    @patch('pybossa.jobs.Message')
    def test_send_mail_sends_mail(self, Message, mail):
        mail_dict = dict(subject='Hello', recipients=['pepito@hotmail.con'],
                         body='Hello Pepito!')
        send_mail(mail_dict)

        mail.send.assert_called_once_with(Message())
        assert mail.send.called

    @with_context
    @patch('pybossa.jobs.mail')
    @patch('pybossa.jobs.Message')
    def test_send_mail_filters_spam(self, Message, mail):
        mail_dict = dict(subject='Hello', recipients=['pepito@fake.com'],
                         body='Hello Pepito!')
        send_mail(mail_dict)

        assert mail.send.called is False

    @with_context
    @patch('pybossa.jobs.mail')
    @patch('pybossa.jobs.Message')
    def test_send_mail_filters_spam_two_emails(self, Message, mail):
        mail_dict = dict(subject='Hello', recipients=['juan@good.com',
                                                      'pepito@fake.com'],
                         body='Hello Pepito!')
        send_mail(mail_dict)

        assert mail.send.called is False
