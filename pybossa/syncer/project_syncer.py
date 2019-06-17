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
import requests
from pybossa.core import project_repo, http_signer
from pybossa.syncer import Syncer, NotEnabled, SyncUnauthorized
from pybossa.syncer.category_syncer import CategorySyncer


class ProjectSyncer(Syncer):
    """Syncs one project with another."""

    _api_endpoint = 'project'
    reserved_keys = (
            'id', 'created', 'updated', 'completed', 'contacted',
            'published', 'secret_key', 'owner_id', 'owners_ids',
            'links', 'link', 'category_id')
    pass_through_keys = ('task_presenter', )
    github_keys = ('pusher', 'ref', 'ref_url', 'timestamp', 'message')

    def sync(self, project):
        target = self.get_target(short_name=project.short_name)
        payload = self._build_payload(project, target)

        if not target:
            return self._create(payload, self.target_key)
        elif self.is_sync_enabled(target):
            target_id = target['id']
            self.cache_target(target, project.short_name)
            res = self._sync(payload, target_id, self.target_key)
            if res.reason == 'FORBIDDEN':
                raise SyncUnauthorized(self.__class__.__name__)
        else:
            raise NotEnabled

        return res

    def undo_sync(self, project):
        target = self.get_target_cache(project.short_name)

        if target:
            payload = dict(info=target['info'])
            target_id = target['id']
            res = self._sync(payload, target_id, self.target_key)
            self.delete_target_cache(project.short_name)
            return res

    def _sync(self, payload, target_id, api_key):
        url = '{}/api/project/{}'.format(
                self.target_url, target_id)
        headers = {'Authorization': api_key}
        res = requests.put(
            url, json=payload, headers=headers, auth=http_signer)
        return res

    def _build_payload(self, project, target=None):
        project_dict = project.dictize()

        if not target:
            payload = self._remove_reserved_keys(project_dict)
        else:
            payload = self._merge_pass_through_keys(
                    project_dict, target)

        payload = self._add_sync_info(payload)
        payload = self._sync_category(project.category_id, payload)
        payload = self._merge_github_keys(project_dict, payload)

        return payload

    def _merge_pass_through_keys(self, project_dict, target):
        payload = {'info': deepcopy(target['info'])}
        for key in self.pass_through_keys:
            value = project_dict['info'].pop(key, None)
            if value:
                payload['info'][key] = value

        return payload

    def _merge_github_keys(self, project_dict, payload):
        for key in self.github_keys:
            value = project_dict['info'].pop(key, None)
            if key in ('ref', 'ref_url') and value:
                payload['info']['sync'][key] = value

        return payload

    def _sync_category(self, category_id, payload):
        category_syncer = CategorySyncer(
                self.target_url, self.target_key)
        category = project_repo.get_category(category_id)
        target_category = category_syncer.get_target(
                name=category.name)

        if target_category:
            payload['category_id'] = target_category['id']
        else:
            res = category_syncer.sync(category)
            if res.ok:
                data = json.loads(res.content)
                payload['category_id'] = data['id']

        return payload

    def get_target_owners(self, project):
        """Get the email addresses of all owners and
        coowners for the target project.

        :param project: a project object
        :return: an list of email addresses
        """
        target = self.get_target(short_name=project.short_name)

        owner_emails = [self.get_user_email(owner_id)
                        for owner_id in target['owners_ids']]

        return [owner_email for owner_email in owner_emails
                if owner_email is not None]

    def get_user_email(self, user_id):
        url = '{}/api/user/{}'.format(self.target_url, user_id)
        headers = {'Authorization': self.target_key}

        try:
            res = requests.get(url, headers=headers)
            user = json.loads(res.content)
            return user['email_addr']
        except:
            return None
