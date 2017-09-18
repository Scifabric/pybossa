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
ProjectSyncer module for syncing projects on different domains.
"""

import json
from datetime import datetime
from socket import gethostname
import requests
from pybossa.syncer import Syncer


class ProjectSyncer(Syncer):
    """Syncs one project with another."""

    RESERVED_KEYS = (
        'id', 'created', 'updated', 'completed',
        'contacted', 'published', 'secret_key',
        'owner_id', 'links', 'link', 'category_id')

    PASS_THROUGH_KEYS = (
        'task_presenter', 'pusher', 'ref', 'ref_url',
        'timestamp')

    @staticmethod
    def get(short_name, url, api_key):
        """GET request to fetch a project object.

        :param short_name: project short name
        :param url: a valid URL,
            ex: https://www.my-domain.com
        :param api_key: the API key for the url
        :return: a project object (dict) or None
        """
        url = '{}/api/project'.format(url)

        params = dict(short_name=short_name,
                      api_key=api_key)

        res = requests.get(url, params=params)
        if res.ok:
            res = json.loads(res.content)
            try:
                return res[0]
            except:
                return None
        else:
            current_app.logger.error(
                'URL: {}, Project: {} - Request Error: {}'
                .format(url, short_name, res.reason))
            return None

    @staticmethod
    def is_sync_enabled(target):
        """Is the target project enabled for syncing?"""
        try:
            return target['info']['sync']['enabled']
        except:
            return False

    def sync(self, project, target_url, target_key):
        """Sync a project with replicated project on
        another domain. Short names must match on each
        domain. If not project exists on the target
        domain, then a new replica project is created.

        :param project: a project object
        :param target_url: the server where the target
            project exists
        :param target_key: the API key for the target
            server to allow the target project to be
            updated
        :return: an HTTP response object
        """
        target = self.get(
            project.short_name, target_url, target_key)

        params = {'api_key': target_key}

        if not target:
            payload = self._build_payload(project, full=True)
            return self._create_new_project(
                project, target_url, params)
        elif self.is_sync_enabled(target):
            target_id = target['id']
            self.cache_target(
                target, target_url, project.short_name)
            payload = self._build_payload(project, target)
            return self._sync(
                payload, target_url, target_id, params)
        else:
            raise Exception('Unauthorized')

    def _sync(self, payload, target_url, target_id, params):
        url = ('{}/api/project/{}'
               .format(target_url, target_id))
        res = requests.put(
            url, data=payload, params=params)
        print res
        return res

    def _create_new_project(self, payload, target_url, params):
        url = '{}/api/project'.format(target_url)
        res = requests.post(
            url, data=payload, params=params)
        return res

    def undo_sync(self, project, target_url, target_key):
        """Undo a project sync action by getting the
        targets cached value and sending a PUT request
        to reset it to it's original state.

        :param project: a project object
        :param target_url: the server where the target
            project exists
        :param target_key: the API key for the target
            server to allow the target project to be
            updated
        :return: an HTTP response object
        """
        target = self.get_target_cache(
            target_url, project.short_name)

        if target:
            params = {'api_key': target_key}
            payload = json.dumps(dict(info=target['info']))
            target_id = target['id']
            res = self._sync(
                payload, target_url, target_id, params)
            self.delete_target_cache(target_url, project.short_name)
            return res
        else:
            return

    def _build_payload(self, project, target=None, full=False):
        project_dict = project.dictize()
        if full:
            payload = self._remove_reserved_keys(project_dict)
        else:
            payload = self._merge_pass_through_keys(
                project_dict, target)

        latest_sync = str(datetime.now())
        source_host = gethostname()
        if payload['info'].get('sync'):
            payload['info']['sync']['latest_sync'] = latest_sync
            payload['info']['sync']['source_host'] = source_host
        else:
            payload['info']['sync'] = dict(
                latest_sync=latest_sync,
                source_host=source_host)

        return json.dumps(payload)

    def _remove_reserved_keys(self, project_dict):
        for key in self.RESERVED_KEYS:
            project_dict.pop(key, None)

        return project_dict

    def _merge_pass_through_keys(self, project, target):
        payload = {'info': target['info']}
        for key in self.PASS_THROUGH_KEYS:
            value = project['info'].pop(key, None)
            if value:
                payload['info'][key] = value

        return payload

    def get_target_owners(self, project, target_url, target_key):
        """
        Get the email addresses of all owners and coowners
        for the target project.

        :param project: a project object
        :param target_url: the server where the target
            project exists
        :param target_key: the API key for the target
        :return: an list of email addresses
        """
        target = self.get(
            project.short_name, target_url, target_key)
        owner = target['owner_id']
        target_id = target['id']
        url = '{}/api/projectcoowner'.format(target_url)
        params = dict(api_key=target_key,
                      project_id=target_id)
        res = requests.get(url, params=params)
        coowners = json.loads(res.content)

        owners = [owner] + coowners
        owner_emails = [
            self.get_user_email(owner, target_url, target_key)
            for owner in owners]
        return owner_emails

    @staticmethod
    def get_user_email(user_id, target_url, target_key):
        url = '{}/api/user/{}'.format(target_url, user_id)
        params = {'api_key': target_key}
        res = requests.get(url, params=params)
        user = json.loads(res.content)
        return user['email_addr']
