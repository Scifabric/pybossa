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
from copy import deepcopy
from datetime import datetime
import requests
from flask import current_app
from pybossa.syncer import Syncer, NotEnabled


class ProjectSyncer(Syncer):
    """Syncs one project with another."""

    RESERVED_KEYS = (
        'id', 'created', 'updated', 'completed', 'contacted',
        'published', 'secret_key', 'owner_id', 'owners_ids', 'links',
        'link', 'category_id')
    PASS_THROUGH_KEYS = ('task_presenter', )
    GITHUB_KEYS = ('pusher', 'ref', 'ref_url', 'timestamp')

    @staticmethod
    def is_sync_enabled(target):
        """Is the target project enabled for syncing?"""
        try:
            return target['info']['sync']['enabled']
        except:
            return False

    def get(self, short_name, api_key):
        """GET request to fetch a project object.

        :param short_name: project short name
        :param api_key: the API key for the url
        :return: a project object (dict) or None
        """
        url = '{}/api/project'.format(self.target_url)
        params = dict(short_name=short_name,
                      api_key=api_key,
                      all=1)
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

    def sync(self, project, target_key, current_user):
        """Sync a project with replicated project on
        another domain. Short names must match on each
        domain. If project does not exist on the target
        domain, then a new replica project is created.

        :param project: a project object
        :param target_key: the API key for the target
            server to allow the target project to be
            updated
        :param current_user: the user that initiated the
            sync
        :return: an HTTP response object
        """
        target = self.get(project.short_name, target_key)
        params = {'api_key': target_key}
        payload = self._build_payload(project=project,
                                      current_user=current_user,
                                      target=target,
                                      full=not target)
        if not target:
            return self._create_new_project(payload, params)
        elif self.is_sync_enabled(target):
            target_id = target['id']
            self.cache_target(target, project.short_name)
            return self._sync(payload, target_id, params)
        else:
            raise NotEnabled

    def _sync(self, payload, target_id, params):
        url = ('{}/api/project/{}'
               .format(self.target_url, target_id))
        headers = {'Content-Type': 'application/json'}
        res = requests.put(
            url, data=payload, params=params, headers=headers)
        return res

    def _create_new_project(self, payload, params):
        url = '{}/api/project'.format(self.target_url)
        res = requests.post(
            url, data=payload, params=params)
        return res

    def undo_sync(self, project, target_key):
        """Undo a project sync action by getting the
        targets cached value and sending a PUT request
        to reset it to it's original state.

        :param project: a project object
        :param target_key: the API key for the target
            server to allow the target project to be
            updated
        :return: an HTTP response object
        """
        target = self.get_target_cache(project.short_name)

        if target:
            params = {'api_key': target_key}
            payload = json.dumps(dict(info=target['info']))
            target_id = target['id']
            res = self._sync(payload, target_id, params)
            self.delete_target_cache(project.short_name)
            return res

    def _build_payload(self, project, current_user,
                       target=None, full=False):
        project_dict = project.dictize()
        if full:
            payload = self._remove_reserved_keys(project_dict)
        else:
            payload = self._merge_pass_through_keys(
                project_dict, target)

        latest_sync = str(datetime.now())
        source_url = current_app.config.get('SERVER_URL')

        payload['info']['sync'] = dict(latest_sync=latest_sync,
                                       source_url=source_url,
                                       syncer=current_user.email_addr,
                                       enabled=False)

        payload = self._merge_github_keys(project_dict, payload)

        return json.dumps(payload)

    def _remove_reserved_keys(self, project_dict):
        for key in self.RESERVED_KEYS:
            project_dict.pop(key, None)

        return project_dict

    def _merge_pass_through_keys(self, project_dict, target):
        payload = {'info': deepcopy(target['info'])}
        for key in self.PASS_THROUGH_KEYS:
            value = project_dict['info'].pop(key, None)
            if value:
                payload['info'][key] = value

        return payload

    def _merge_github_keys(self, project_dict, payload):
        for key in self.GITHUB_KEYS:
            value = project_dict['info'].pop(key, None)
            if key in ('ref', 'ref_url') and value:
                payload['info']['sync'][key] = value

        return payload

    def get_target_owners(self, project, target_key):
        """Get the email addresses of all owners and
        coowners for the target project.

        :param project: a project object
        :param target_key: the API key for the target
        :return: an list of email addresses
        """
        target = self.get(project.short_name, target_key)

        owner_emails = [
            self.get_user_email(owner_id, target_key)
            for owner_id in target['owners_ids']]

        return [owner_email for owner_email in owner_emails
                if owner_email is not None]

    def get_user_email(self, user_id, target_key):
        url = '{}/api/user/{}'.format(self.target_url, user_id)
        params = {'api_key': target_key}

        try:
            res = requests.get(url, params=params)
            user = json.loads(res.content)
            return user['email_addr']
        except:
            return None
