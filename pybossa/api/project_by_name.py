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

from flask import request
from werkzeug.exceptions import NotFound, BadRequest
from pybossa.cache import memoize
from pybossa.core import project_repo, timeouts
from pybossa.error import ErrorStatus
from pybossa.api.project import ProjectAPI


error = ErrorStatus()


def methodview_altkey(key_to_oid):
    def decorator(cls):

        def rt_handler(self, key):
            method = request.method
            if not key:
                return error.format_exception(BadRequest('Invalid Key'),
                                              cls.__name__.lower(), method)
            oid = key_to_oid(key)
            if not oid:
                return error.format_exception(NotFound('Object not found'),
                                              cls.__name__.lower(), method)
            return getattr(super(cls, self), method.lower())(oid)

        for action in ('get', 'put', 'delete'):
            setattr(cls, action, rt_handler)
        return cls

    return decorator


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def project_name_to_oid(shortname):
    project = project_repo.get_by_shortname(shortname)
    return project.id if project else None


@methodview_altkey(project_name_to_oid)
class ProjectByNameAPI(ProjectAPI):

    pass
