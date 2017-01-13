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
PYBOSSA messages.

This module exports the following variables:
    * SUCCESS
    * ERROR
    * WARNING
    * FORBIDDEN
    * NOTFOUND
    * BADREQUEST
    * INTERNALSERVERERROR
    * NOTFOUND
    * UNAUTHORIZED

"""
from werkzeug.exceptions import Forbidden, Unauthorized, InternalServerError
from werkzeug.exceptions import NotFound, BadRequest

__all__ = ['SUCCESS', 'ERROR', 'WARNING', 'FORBIDDEN', 'NOTFOUND', 'BADREQUEST',
           'INFO', 'NOTFOUND', 'INTERNALSERVERERROR', 'UNAUTHORIZED']

SUCCESS = "success"

ERROR = "error"

WARNING = "warning"

INFO = "info"

FORBIDDEN = Forbidden.description

NOTFOUND = NotFound.description

BADREQUEST = BadRequest.description

INTERNALSERVERERROR = InternalServerError.description

UNAUTHORIZED = Unauthorized.description

assert SUCCESS
assert ERROR
assert WARNING
assert FORBIDDEN
assert NOTFOUND
assert BADREQUEST
assert INTERNALSERVERERROR
assert UNAUTHORIZED
