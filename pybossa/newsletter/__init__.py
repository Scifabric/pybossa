# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
"""PyBossa module for subscribing users to Mailchimp lists."""

import mailchimp
from mailchimp import Error


class Newsletter(object):

    """Newsletter class to handle mailchimp subscriptions."""

    def __init__(self, app=None):
        """Init method for flask extensions."""
        self.app = app
        if app is not None:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        """Configure newsletter Mailchimp client."""
        self.app = app
        self.client = mailchimp.Mailchimp(app.config.get('MAILCHIMP_API_KEY'))
        self.list_id = app.config.get('MAILCHIMP_LIST_ID')

    def is_initialized(self):
        return self.app is not None

    def ask_user_to_subscribe(self, user):
        return (self.is_initialized() and
                user.newsletter_prompted is False and
                self.is_user_subscribed(user.email_addr) is False)

    def is_user_subscribed(self, email, list_id=None):
        """Check if user is subscribed or not."""
        try:
            if list_id is None:
                list_id = self.list_id

            res = self.client.lists.member_info(list_id, [{'email': email}])
            return (res.get('success_count') == 1 and
                    res['data'][0]['email'] == email)
        except Error as e:
            msg = 'MAILCHIMP: An error occurred: %s - %s' % (e.__class__, e)
            self.app.logger.error(msg)
            raise

    def subscribe_user(self, user, list_id=None, old_email=None):
        """Subscribe, update a user of a mailchimp list."""
        try:
            update_existing = False
            if list_id is None:
                list_id = self.list_id
            merge_vars = {'FNAME': user.fullname}
            if old_email:
                email = {'email': old_email}
                merge_vars['new-email'] = user.email_addr
                update_existing = self.is_user_subscribed(old_email)
            else:
                email = {'email': user.email_addr}

            self.client.lists.subscribe(list_id, email, merge_vars,
                                        update_existing=update_existing)
        except Error, e:
            msg = 'MAILCHIMP: An error occurred: %s - %s' % (e.__class__, e)
            self.app.logger.error(msg)
            raise
