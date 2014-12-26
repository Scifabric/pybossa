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
"""
PyBossa api module for domain object APP via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * projects,

"""
from flask.ext.login import current_user
from api_base import APIBase
from pybossa.model.app import App
import pybossa.cache.apps as cached_apps
from pybossa.cache.categories import get_all as get_categories
from pybossa.util import is_reserved_name
from pybossa.core import auditlog_repo
from pybossa.auditlogger import AuditLogger

auditlogger = AuditLogger(auditlog_repo, caller='api')


class AppAPI(APIBase):

    """
    Class for the domain object App.

    It refreshes automatically the cache, and updates the project properly.

    """

    __class__ = App

    def _create_instance_from_request(self, data):
        inst = super(AppAPI, self)._create_instance_from_request(data)
        default_category = get_categories()[0]
        inst.category_id = default_category.id
        return inst

    def _refresh_cache(self, obj):
        cached_apps.delete_app(obj.short_name)

    def _update_object(self, obj):
        if not current_user.is_anonymous():
            obj.owner_id = current_user.id

    def _validate_instance(self, project):
        if project.short_name and is_reserved_name('app', project.short_name):
            msg = "Project short_name is not valid, as it's used by the system."
            raise ValueError(msg)

    def _log_changes(self, old_project, new_project):
        auditlogger.add_log_entry(old_project, new_project, current_user)
