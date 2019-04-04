# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
PyBossa api module for exposing domain object TaskRun for completed tasks via an API.

This package adds GET method for:
    * completedtaskruns

"""
from flask import request, Response
from flask_login import current_user
from api_base import APIBase
from pybossa.model.task_run import TaskRun
from pybossa.error import ErrorStatus
from pybossa.core import task_repo
from werkzeug.exceptions import MethodNotAllowed, Unauthorized
from pybossa.util import jsonpify, crossdomain
from pybossa.core import ratelimits
from pybossa.ratelimit import ratelimit

cors_headers = ['Content-Type', 'Authorization']
error = ErrorStatus()

# cloned from AppAPI
class CompletedTaskRunAPI(APIBase):

    """
    Class for the domain object TaskRun.

    """

    __class__ = TaskRun

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def get(self, oid):
        """Get taskruns for all completed tasks and gold tasks. Need admin access"""
        try:
            if not (current_user.is_authenticated and current_user.admin):
                raise Unauthorized("Insufficient privilege to the request")

            # set filter from args
            filters = {}
            for k in request.args.keys():
                if k not in ['limit', 'offset', 'api_key', 'last_id']:
                    # 'exported' column belongs to Task class
                    # ignore it for attr check in TaskRun class
                    # but add it to filter so that its checked
                    # against Task class in filter_completed_taskruns_gold_taskruns_by
                    if k not in ['exported']:
                        # Raise an error if the k arg is not a column
                        getattr(self.__class__, k)
                    filters[k] = request.args[k]

            # set limit, offset
            limit, offset, orderby = self._set_limit_and_offset()
            last_id = request.args.get('last_id', 0)
            results = task_repo.filter_completed_taskruns_gold_taskruns_by(
                limit=limit, offset=offset, last_id=last_id, **filters)
            json_response = self._create_json_response(results, oid)
            return Response(json_response, mimetype='application/json')
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
            action='GET')

    def post(self):
        raise MethodNotAllowed(valid_methods=['GET'])

    def delete(self, oid=None):
        raise MethodNotAllowed(valid_methods=['GET'])

    def put(self, oid=None):
        raise MethodNotAllowed(valid_methods=['GET'])
