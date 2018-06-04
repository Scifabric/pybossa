# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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

class HttpSigner(object):
    def __init__(self, secret, header):
        self.secret = secret
        self.header = header

    def __call__(self, request):
        if not self.secret:
            return request

        signature = self.secret
        request.headers[self.header] = signature
        return request

    def valid(self, request):
        signature = request.headers.get(self.header)

        if not signature or not self.secret:
            return False

        return self.secret == signature
