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
import requests


class ProjectSyncer(object):
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
        :param url: a valid protocol and hostname,
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
    def is_sync_enabled(project):
        """Is the target project enabled for syncing?"""
        try:
            return project.info['sync']['enabled']
        except:
            return False

    def sync(self, project):
        """Sync a project with replicated project on
        another domain. Short names must match on each
        domain. If not project exists on the target
        domain, then a new replica project is created.

        :param project: a project object
        :return: an HTTP response object
        """
        target_url = project.info.get('sync', {}).get('target_url')
        target_key = project.info.get('sync', {}).get('target_key')
        target = self.get(
            project.short_name, target_url, target_key)
        if not target:
            self._create_new_project(project)
        elif self.is_sync_enabled(project):
            target_id = target['id']
            self._cache_target(target)
            payload = self._build_payload(project, target)
            target_url = ('{}/api/project/{}'
                          .format(target_url, target_id))
            params = {'api_key': target_key}
            res = requests.put(
                target_url, data=payload, params=params)
            return res
        else:
            raise Exception('Unauthorized')

    def _build_payload(self, project, target, full=False):
        project_dict = project.dictize()
        if full:
            payload = self._remove_reserved_keys(project_dict)
        else:
            payload = self._merge_pass_through_keys(
                project_dict, target)

        latest_sync = str(datetime.now())
        if payload['info'].get('sync'):
            payload['info']['sync']['latest_sync'] = latest_sync
        else:
            payload['info']['sync'] = dict(
                latest_sync=latest_sync)

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

###############################################################################

    def _create_new_project(self, payload):
        """Create new project at the target URL."""
        return payload


    def sync_all(self):
        """Sync all target projects with the source project."""
        return [self.sync(target) for target in self.targets]

    def undo_sync(self, target):
        cached_target = self._fetch_cached_target(target)
        return self._sync(cached_target, target)

    def _cache_target(self, target):
        pass

    def _fetch_cached_target(self, target):
        pass

    def _get_target_projects(self):
        print 'get target projects'
        return {
            target['url']: self._get(target['url'], self.short_name, target['api_key'])
            for target in self.targets}
