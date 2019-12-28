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
from werkzeug.exceptions import BadRequest, Forbidden
from flask_login import current_user
from .api_base import APIBase
from pybossa.model.project import Project
from pybossa.cache.categories import get_all as get_categories
from pybossa.util import is_reserved_name
from pybossa.core import auditlog_repo, result_repo
from pybossa.auditlogger import AuditLogger

auditlogger = AuditLogger(auditlog_repo, caller='api')


class ProjectAPI(APIBase):

    """
    Class for the domain object Project.

    It refreshes automatically the cache, and updates the project properly.

    """

    __class__ = Project
    reserved_keys = set(['id', 'created', 'updated', 'completed', 'contacted',
                         'published', 'secret_key'])
    private_keys = set(['secret_key'])

    def _create_instance_from_request(self, data):
        inst = super(ProjectAPI, self)._create_instance_from_request(data)
        category_ids = [c.id for c in get_categories()]
        default_category = get_categories()[0]
        inst.category_id = default_category.id
        if 'category_id' in list(data.keys()):
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

    def _validate_instance(self, project):
        if project.short_name and is_reserved_name('project', project.short_name):
            msg = "Project short_name is not valid, as it's used by the system."
            raise ValueError(msg)

    def _log_changes(self, old_project, new_project):
        auditlogger.add_log_entry(old_project, new_project, current_user)

    def _forbidden_attributes(self, data):
        for key in list(data.keys()):
            if key in self.reserved_keys:
                if key == 'published':
                    raise Forbidden('You cannot publish a project via the API')
                raise BadRequest("Reserved keys in payload")

    def _filter_private_data(self, data):
        tmp = copy.deepcopy(data)
        public = Project().public_attributes()
        public.append('link')
        public.append('links')
        public.append('stats')
        for key in list(tmp.keys()):
            if key not in public:
                del tmp[key]
        for key in list(tmp['info'].keys()):
            if key not in Project().public_info_keys():
                del tmp['info'][key]
        return tmp

    def _select_attributes(self, data):
        if current_user.is_anonymous:
            data = self._filter_private_data(data)
            return data
        if (current_user.is_authenticated and
                (current_user.id in data['owners_ids'] or current_user.admin)):
            return data
        else:
            data = self._filter_private_data(data)
            return data
