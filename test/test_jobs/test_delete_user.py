# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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
from default import Test, with_context, FakeResponse
from factories import UserFactory
from pybossa.jobs import delete_account, send_mail
from pybossa.core import user_repo
from mock import patch
from flask import current_app

@patch('pybossa.jobs.mail')
@patch('pybossa.jobs.Message')
class TestDeleteAccount(Test):

    @with_context
    @patch('requests.delete')
    def test_send_mail_creates_message_mailchimp_error(self, mailchimp, Message, mail):
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            user = UserFactory.create()
            user_id = user.id
            brand = 'PYBOSSA'
            subject = '[%s]: Your account has been deleted' % brand
            body = """Hi,\nYour account and personal data has been deleted from %s.""" % brand
            body += '\nWe could not delete your Mailchimp account, please contact us to fix this issue.'

            recipients = [user.email_addr, 'admin@broken.com']
            mail_dict = dict(recipients=recipients,
                             subject=subject,
                             body=body)

            delete_account(user.id)
            Message.assert_called_once_with(**mail_dict)
            mail.send.assert_called_once_with(Message())
            user = user_repo.get(user_id)
            assert user is None

    @with_context
    @patch('requests.delete')
    def test_send_mail_creates_message_mailchimp_ok(self, mailchimp, Message, mail):
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1}):
            user = UserFactory.create()
            user_id = user.id
            brand = 'PYBOSSA'
            subject = '[%s]: Your account has been deleted' % brand
            body = """Hi,\nYour account and personal data has been deleted from %s.""" % brand

            recipients = [user.email_addr, 'admin@broken.com']
            mail_dict = dict(recipients=recipients,
                             subject=subject,
                             body=body)

            mailchimp.side_effect = [FakeResponse(text=json.dumps(dict(status=204)),
                                                 json=lambda : '',
                                               status_code=204)]
            delete_account(user.id)
            Message.assert_called_once_with(**mail_dict)
            mail.send.assert_called_once_with(Message())
            user = user_repo.get(user_id)
            assert user is None

    @with_context
    @patch('requests.delete')
    def test_send_mail_creates_message_mailchimp_disquss(self, mailchimp, Message, mail):
        with patch.dict(self.flask_app.config, {'MAILCHIMP_API_KEY': 'k-3',
                                                'MAILCHIMP_LIST_ID': 1,
                                                'DISQUS_SECRET_KEY': 'key'}):
            user = UserFactory.create()
            user_id = user.id
            brand = 'PYBOSSA'
            subject = '[%s]: Your account has been deleted' % brand
            body = """Hi,\nYour account and personal data has been deleted from %s.""" % brand
            body += '\nDisqus does not provide an API method to delete your account. You will have to do it by hand yourself in the disqus.com site.'

            recipients = [user.email_addr, 'admin@broken.com']
            mail_dict = dict(recipients=recipients,
                             subject=subject,
                             body=body)

            mailchimp.side_effect = [FakeResponse(text=json.dumps(dict(status=204)),
                                                 json=lambda : '',
                                               status_code=204)]
            delete_account(user.id)
            Message.assert_called_once_with(**mail_dict)
            mail.send.assert_called_once_with(Message())
            user = user_repo.get(user_id)
            assert user is None
