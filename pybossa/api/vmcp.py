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
PyBossa api module for exposing VMCP via an API.

This package signs via API a request from CernVM plugin.

"""
import os
import json
import pybossa.vmcp
from flask import Response, request, current_app
from api_base import APIBase, cors_headers
from werkzeug.exceptions import MethodNotAllowed
from pybossa.core import ratelimits
from pybossa.util import jsonpify, crossdomain
from pybossa.ratelimit import ratelimit


class VmcpAPI(APIBase):

    """Class for CernVM plugin api.

    Returns signed object to start a CernVM instance.

    """

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def get(self, oid=None):
        """Return signed VMCP for CernVM requests."""
        if current_app.config.get('VMCP_KEY') is None:
            message = "The server is not configured properly, contact the admins"
            error = self._format_error(status_code=501, message=message)
            return Response(json.dumps(error), status=error['status_code'],
                            mimetype='application/json')

        pkey = (current_app.root_path + '/../keys/' +
                current_app.config.get('VMCP_KEY'))
        if not os.path.exists(pkey):
            message = "The server is not configured properly (private key is missing), contact the admins"
            error = self._format_error(status_code=501, message=message)
            return Response(json.dumps(error), status=error['status_code'],
                            mimetype='application/json')

        if request.args.get('cvm_salt') is None:
            message = "cvm_salt parameter is missing"
            error = self._format_error(status_code=415, message=message)
            return Response(json.dumps(error), status=error['status_code'],
                            mimetype='application/json')

        salt = request.args.get('cvm_salt')
        data = request.args.copy()
        signed_data = pybossa.vmcp.sign(data, salt, pkey)
        return Response(json.dumps(signed_data), 200, mimetype='application/json')

    def _format_error(self, status_code=None, message=None):
        return dict(action=request.method,
                    status="failed",
                    status_code=status_code,
                    target='vmcp',
                    exception_cls='vmcp',
                    exception_msg=message)


    @ratelimit(limit=ratelimits.get('LIMIT'), per=ratelimits.get('PER'))
    def post(self):
        raise MethodNotAllowed
