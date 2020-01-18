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

"""
Syncer module for syncing objects on different domains.
"""

import json
import requests
from datetime import datetime
from flask import current_app
from flask_login import current_user
from werkzeug.exceptions import Unauthorized
from pybossa.core import sentinel, http_signer


ONE_WEEK = 60 * 60 * 24 * 7


class Syncer(object):
    """Syncs one object with another."""

    _api_endpoint = ''
    sync_key = 'pybossa::sync::{}::target_url:{}::short_name:{}'
    cache_timeout = ONE_WEEK

    def __init__(self, target_url, target_key):
        """Initialize a Syncer.

        :param target_url: The target URL to sync with
        :param target_key: The target api key
        """
        self.target_url = target_url
        self.target_key = target_key
        self.syncer = current_user

    @staticmethod
    def is_sync_enabled(target):
        """Is the target enabled for syncing?"""
        try:
            return target['info']['sync']['enabled']
        except Exception:
            return False

    def get_target(self, **params):
        """GET request to fetch an object on the
        target server.

        :param params: Additional parameters to
            add to the request
        :return: A domain object or None
        """
        url = '{}/api/{}'.format(
                self.target_url, self._api_endpoint)

        if not params:
            params = {}
        headers = {
            'Authorization': self.target_key
        }

        params['all'] = 1
        res = requests.get(url, params=params, headers=headers)

        if res.ok:
            data = json.loads(res.content)

            if len(data) == 0:
                return None
            elif len(data) == 1:
                return data[0]
            else:
                current_app.logger.error(
                        'More than one target returned: {}, {}: {} - Content: {}'
                        .format(
                            url, self._api_endpoint, params, res.content))
                return None
        else:
            current_app.logger.error(
                    'URL: {}, {}: {} - Request Error: {}'
                    .format(
                        url, self._api_endpoint, params, res.reason))
            return None

    def sync(self, obj):
        """Sync an object with a replicated object on
        another domain. If object does not exist on the
        target domain, then a new replica object is
        created.

        :param obj: A domain object
        :return: an HTTP response object
        """
        raise NotImplementedError('')

    def undo_sync(self, obj):
        """Undo a sync action by getting the target's
        cached value and sending a PUT request to
        reset it to it's original state.

        :param obj: A domain object
        :return: an HTTP response object
        """
        raise NotImplementedError('')

    def _create(self, payload, api_key):
        url = '{}/api/{}'.format(
            self.target_url, self._api_endpoint)
        headers = {'Authorization': api_key}
        res = requests.post(
            url, json=payload, headers=headers, auth=http_signer)
        return res

    def get_target_user(self, user_id, api_key):
        url = '{}/api/user/{}'.format(
            self.target_url, user_id)
        headers = {'Authorization': api_key}
        res = requests.get(
            url, headers=headers)
        return res

    def cache_target(self, target, target_id):
        """Cache target.

        :param target: a domain object dict
        :param target_id: any identifier that
            can be used to create a unique key
        """
        target = json.dumps(target)
        sentinel.master.setex(
                self._get_key(target_id),
                self.cache_timeout,
                target)

    def get_target_cache(self, target_id):
        """Get cached target value.

        :param target_id: the identifier used
            to create a unique key
        :return: a dict of the target
        """
        target = sentinel.master.get(self._get_key(target_id))

        if target:
            return json.loads(target)
        else:
            return

    def delete_target_cache(self, target_id):
        """Delete cached target value.

        :param target_id: the identifier used
            to create a unique key
        """
        sentinel.master.delete(self._get_key(target_id))

    def _get_key(self, target_id):
        target_id = target_id.encode('utf-8')
        return self.sync_key.format(
                self.__class__.__name__,
                self.target_url,
                target_id)

    def _add_sync_info(self, payload, enabled=False):
        latest_sync = str(datetime.now())
        source_url = current_app.config.get('SERVER_URL')

        sync_info = dict(latest_sync=latest_sync,
                         source_url=source_url,
                         syncer=self.syncer.email_addr,
                         enabled=enabled)

        payload['info']['sync'] = sync_info
        return payload

    def _remove_reserved_keys(self, object_dict):
        for key in self.reserved_keys:
            object_dict.pop(key, None)

        return object_dict


class NotEnabled(Exception):
    """An exception indicating that an error
    has occurred where a syncer tried to sync,
    but could not due to the target not being
    enabled for syncing.
    """
    pass


class SyncUnauthorized(Unauthorized):
    """An exception indicating that the user
    was not authorized to perform a sync due
    to the target server returning an error.
    """
    def __init__(self, sync_type):
        Unauthorized.__init__(self)
        self.sync_type = sync_type
