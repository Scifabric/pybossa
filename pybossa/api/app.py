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
from flask import redirect, url_for, request
from flask.ext.login import current_user
from api_base import APIBase
from pybossa.model.project import Project
import pybossa.cache.projects as cached_projects
from pybossa.cache.categories import get_all as get_categories
from pybossa.util import is_reserved_name
from pybossa.core import auditlog_repo
from pybossa.auditlogger import AuditLogger

auditlogger = AuditLogger(auditlog_repo, caller='api')


class AppAPI(APIBase):

    """
    Class for the domain object Project.

    It refreshes automatically the cache, and updates the project properly.

    """

    __class__ = Project

    def get(self, oid):
        return redirect(url_for('api.api_project', oid=oid))

    def post(self):
        return redirect(url_for('api.api_project'), code=307)

    def delete(self, oid):
        return redirect(url_for('api.api_project', oid=oid), code=307)

    def put(self, oid):
        api_key = request.args.get('api_key')
        return redirect(url_for('api.api_project',
                                oid=oid,
                                api_key=api_key), code=307)
