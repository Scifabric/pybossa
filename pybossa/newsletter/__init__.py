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
"""PyBossa module for subscribing users to Mailchimp lists."""

import mailchimp


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

    def subscribe_user(self, user, list_id=None):
        """Subscribe a user to a mailchimp list."""
        try:
            if list_id is None:
                list_id = self.list_id
            self.client.lists.subscribe(list_id, {'email': user.email_addr},
                                                 {'FNAME': user.fullname})
        except mailchimp.Error, e:
            msg = 'MAILCHIMP: An error occurred: %s - %s' % (e.__class__, e)
            self.app.logger.error(msg)
