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
PyBossa api module for exposing domain object TaskRun via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * task_runs

"""
from flask import request, current_app
from flask.ext.login import current_user
from api_base import APIBase
from pybossa import model

class RunDataAPI(APIBase):
    __class__ = model.RunData

    def _query_filter_args(self, request):
        res = APIBase._query_filter_args(self, request)
        for key in res.keys():
            if res[key] == 'null':
                res[key] = None
        if res.get('user_id', None) == '-1':
            del res['user_id']
            if not current_user.is_anonymous():
                res['user_id'] = current_user.id
            else:
                res['user_ip'] = request.remote_addr
        return res

    def _update_object(self, obj):
        if obj.user_id is not None:
            obj.user_id = None
            if not current_user.is_anonymous():
                obj.user = current_user
            else:
                obj.user_ip = request.remote_addr
