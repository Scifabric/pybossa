# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2016 Scifabric LTD.
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

INVALID_HEADER_MISSING = {'code': 'invalid_header',
                          'description': 'Missing Authorization header'}

INVALID_HEADER_BEARER = {'code': 'invalid_header',
                         'description': 'Authorization header \
                         must start with Bearer'}

INVALID_HEADER_TOKEN = {'code': 'invalid_header',
                        'description': 'Token not found'}

INVALID_HEADER_BEARER_TOKEN = {'code': 'invalid_header',
                               'description': 'Authorization header must \
                               be Bearer + \\s + token'}

WRONG_PROJECT_SIGNATURE = {'code': 'Wrong project',
                           'description': 'Signature verification failed'}

DECODE_ERROR_SIGNATURE = {'code': 'Decode error',
                          'description': 'Signature verification failed'}
