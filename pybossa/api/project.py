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
"""
PYBOSSA api module for domain object APP via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * projects,

"""
import copy
from werkzeug.exceptions import BadRequest, Forbidden, Unauthorized
from flask import current_app, request
from flask_login import current_user
from api_base import APIBase
from pybossa.model.project import Project
from pybossa.cache.categories import get_all as get_categories
from pybossa.util import is_reserved_name, description_from_long_description
from pybossa.core import auditlog_repo, result_repo, http_signer
from pybossa.auditlogger import AuditLogger
from pybossa.data_access import ensure_user_assignment_to_project, set_default_amp_store

auditlogger = AuditLogger(auditlog_repo, caller='api')


class ProjectAPI(APIBase):

    """
    Class for the domain object Project.

    It refreshes automatically the cache, and updates the project properly.

    """

    __class__ = Project
    reserved_keys = set(['id', 'created', 'updated', 'completed', 'contacted', 'secret_key'])
    private_keys = set(['secret_key'])
    restricted_keys = set()

    def _preprocess_post_data(self, data):
        # set amp_store default as true when not passed as input param
        amp_config = data.get('info', {}).get('annotation_config', {}).get('amp_store')
        if amp_config is None:
            set_default_amp_store(data)
        # clean up description and long description
        long_desc = data.get("long_description")
        desc = data.get("description")
        if not long_desc and not desc:
            raise BadRequest("description or long description required")
        if not long_desc:
            data["long_description"] = desc
        if not desc:
            data["description"] = description_from_long_description(desc, long_desc)
        # set default data_access
        if not data.get('info', {}).get("data_access"):
            data["info"] = data.get("info", {})
            # set to least restrictive, will overwrite when saved
            data["info"]["data_access"] = ["L4"]

    def _create_instance_from_request(self, data):
        # password required if not syncing
        sync_json = data["info"].get("sync", {})
        # keys added when syncing
        sync_keys = ("latest_sync", "source_url", "syncer")
        sync = all(sync_key in sync_json for sync_key in sync_keys)
        password = data.pop("password", "")
        if not (sync or password) or (sync and "passwd_hash" not in data["info"]):
            raise BadRequest("password required")
        inst = super(ProjectAPI, self)._create_instance_from_request(data)
        if not sync:
            # set password if not syncing
            inst.set_password(password)
        category_ids = [c.id for c in get_categories()]
        default_category = get_categories()[0]
        inst.category_id = default_category.id
        if 'category_id' in data.keys():
            if int(data.get('category_id')) in category_ids:
                inst.category_id = data.get('category_id')
            else:
                raise BadRequest("category_id does not exist")
        return inst

    def _update_object(self, obj):
        if not current_user.is_anonymous:
            obj.owner_id = current_user.id
            owners = obj.owners_ids or []
            if current_user.id not in owners:
                owners.append(current_user.id)
            obj.owners_ids = owners

    def _update_attribute(self, new, old):
        for key, value in old.info.iteritems():
            if not new.info.get(key):
                new.info[key] = value

    def _validate_instance(self, project):
        if project.short_name and is_reserved_name('project', project.short_name):
            msg = "Project short_name is not valid, as it's used by the system."
            raise ValueError(msg)
        ensure_user_assignment_to_project(project)

    def _log_changes(self, old_project, new_project):
        auditlogger.add_log_entry(old_project, new_project, current_user)

    def _forbidden_attributes(self, data):
        for key in data.keys():
            if key in self.reserved_keys:
                raise BadRequest("Reserved keys in payload")

    def _restricted_attributes(self, data):
        if (current_user.is_authenticated and
            not current_user.admin and
            not http_signer.valid(request)):

            for key in data.keys():
                self._raise_if_restricted(key, data)

    @classmethod
    def _raise_if_restricted(cls, key, data, restricted_keys=None):
        if not restricted_keys:
            restricted_keys = list(cls.restricted_keys)

        for restricted_key in restricted_keys:
            split_key = restricted_key.split('::', 1)
            restricted_key = split_key.pop(0)
            if key == restricted_key:
                if isinstance(data, dict) and split_key:
                    for k in data[key].keys():
                        cls._raise_if_restricted(
                            k, data[key], split_key)
                else:
                    raise Unauthorized(
                        'Restricted key in payload '
                        '(Admin privilege required)')

    def _filter_private_data(self, data):
        tmp = copy.deepcopy(data)
        public = Project().public_attributes()
        public.append('link')
        public.append('links')
        public.append('stats')
        for key in tmp.keys():
            if key not in public:
                del tmp[key]
        for key in tmp['info'].keys():
            if key not in Project().public_info_keys():
                del tmp['info'][key]
        return tmp

    def _select_attributes(self, data):
        if (current_user.is_authenticated and
                (current_user.id in data['owners_ids'] or
                    current_user.admin or current_user.subadmin)):
            return data
        else:
            data = self._filter_private_data(data)
            return data
