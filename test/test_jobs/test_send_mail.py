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

from pybossa.jobs import send_mail
from mock import patch

@patch('pybossa.jobs.mail')
@patch('pybossa.jobs.Message')
class TestSendMailJob(object):

    def test_send_mail_craetes_message(self, Message, mail):
        mail_dict = dict(subject='Hello', recipients=['pepito@hotmail.con'],
                         body='Hello Pepito!')
        send_mail(mail_dict)
        Message.assert_called_once_with(**mail_dict)


    def test_send_mail_sends_mail(self, Message, mail):
        mail_dict = dict(subject='Hello', recipients=['pepito@hotmail.con'],
                         body='Hello Pepito!')
        send_mail(mail_dict)

        mail.send.assert_called_once_with(Message())
