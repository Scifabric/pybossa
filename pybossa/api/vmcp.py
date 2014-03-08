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
from pybossa.util import jsonpify, crossdomain
from pybossa.ratelimit import ratelimit


class VmcpAPI(APIBase):

    """Class for CernVM plugin api.

    Returns signed object to start a CernVM instance.

    """

    @jsonpify
    @crossdomain(origin='*', headers=cors_headers)
    @ratelimit(limit=300, per=15 * 60)
    def get(self, id):
        """Return signed VMCP for CernVM requests."""
        error = dict(action=request.method,
                     status="failed",
                     status_code=None,
                     target='vmcp',
                     exception_cls='vmcp',
                     exception_msg=None)
        try:
            if current_app.config.get('VMCP_KEY'):
                pkey = (current_app.root_path + '/../keys/' +
                        current_app.config.get('VMCP_KEY'))
                if not os.path.exists(pkey):
                    raise IOError
            else:
                raise KeyError
            if request.args.get('cvm_salt'):
                salt = request.args.get('cvm_salt')
            else:
                raise AttributeError
            data = request.args.copy()
            signed_data = pybossa.vmcp.sign(data, salt, pkey)
            return Response(json.dumps(signed_data),
                            200,
                            mimetype='application/json')

        except KeyError:
            error['status_code'] = 501
            error['exception_msg'] = ("The server is not configured properly, \
                                      contact the admins")
            return Response(json.dumps(error), status=error['status_code'],
                            mimetype='application/json')
        except IOError:
            error['status_code'] = 501
            error['exception_msg'] = ("The server is not configured properly \
                                      (private key is missing), contact the \
                                      admins")
            return Response(json.dumps(error), status=error['status_code'],
                            mimetype='application/json')

        except AttributeError:
            error['status_code'] = 415
            error['exception_msg'] = "cvm_salt parameter is missing"
            return Response(json.dumps(error), status=error['status_code'],
                            mimetype='application/json')

    def post(self):
        raise MethodNotAllowed
