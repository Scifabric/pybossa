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
"""PYBOSSA module for subscribing users to Mailchimp lists."""

import json
import hashlib
import requests
from requests.auth import HTTPBasicAuth


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
        if app.config.get('MAILCHIMP_API_KEY'):
            self.dc = app.config.get('MAILCHIMP_API_KEY').split('-')[1]
            self.root = 'https://%s.api.mailchimp.com/3.0' % self.dc
            self.auth = HTTPBasicAuth('user', app.config.get('MAILCHIMP_API_KEY'))
            self.list_id = app.config.get('MAILCHIMP_LIST_ID')

    def is_initialized(self):
        return self.app is not None

    def ask_user_to_subscribe(self, user):
        return (user.newsletter_prompted is False and
                self.is_user_subscribed(user.email_addr)[0] is False)

    def get_email_hash(self, email):
        """Return MD5 user email hash."""
        self.md5 = hashlib.md5()
        self.md5.update(str(email).encode('utf-8'))
        return self.md5.hexdigest()

    def is_user_subscribed(self, email, list_id=None):
        """Check if user is subscibed or not."""
        if list_id is None:
            list_id = self.list_id
        url = '%s/lists/%s/members/%s' % (self.root,
                                          list_id,
                                          self.get_email_hash(email))
        res = requests.get(url, auth=self.auth)
        res = res.json()
        if res['status'] == 200:
            return True, res
        else:
            return False, res

    def delete_user(self, email, list_id=None):
        """Delete user from list_id."""
        if list_id is None:
            list_id = self.list_id
        url = '%s/lists/%s/members/%s' % (self.root,
                                          list_id,
                                          self.get_email_hash(email))
        res = requests.delete(url, auth=self.auth)
        if res.status_code == 204:
            return True
        else:
            return False

    def subscribe_user(self, user, list_id=None, update=False):
        """Subscribe, update a user of a mailchimp list."""
        if list_id is None:
            list_id = self.list_id
        url = '%s/lists/%s/members/' % (self.root,
                                        list_id)
        data = dict(email_address=user.email_addr,
                    status='pending',
                    merge_fields=dict(FNAME=user.fullname)
                    )
        if update is False:
            res = requests.post(url, data=json.dumps(data),
                                headers={'content-type': 'application/json'},
                                auth=self.auth)
        else:
            data['status_if_new'] = 'pending'
            url = '%s/lists/%s/members/%s' % (self.root,
                                              list_id,
                                              self.get_email_hash(user.email_addr))

            res = requests.put(url, data=json.dumps(data),
                               headers={'content-type': 'application/json'},
                               auth=self.auth)
        return res.json()
