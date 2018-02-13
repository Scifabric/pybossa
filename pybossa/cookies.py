# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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
"""Cookie module for PYBOSSA."""
from itsdangerous import SignatureExpired


class CookieHandler(object):

    """Cookie Class handler for PYBOSSA."""

    def __init__(self, request, signer, expiration=1200):
        """Init method."""
        self.request = request
        self.signer = signer
        self.expiration = expiration

    def _create_or_update_cookie(self, project, user):
        """Create or update cookie."""
        cookie_name = '%spswd' % project.short_name
        cookie = self.request.cookies.get(cookie_name)
        try:
            cookie = self.signer.loads(cookie, max_age=self.expiration) if cookie else []
        except SignatureExpired:
            cookie = []
        if user not in cookie:
            cookie.append(user)
        cookie = self.signer.dumps(cookie)
        return cookie

    def add_cookie_to(self, response, project, user):
        """Add cookie to response."""
        cookie_name = '%spswd' % project.short_name
        cookie = self._create_or_update_cookie(project, user)
        response.set_cookie(cookie_name, cookie, max_age=self.expiration)
        return response

    def get_cookie_from(self, project):
        """Get cookie from a project."""
        cookie_name = '%spswd' % project.short_name
        signed_cookie = self.request.cookies.get(cookie_name)
        try:
            cookie = self.signer.loads(signed_cookie, max_age=self.expiration) if signed_cookie else []
        except SignatureExpired:
            cookie = []
        return cookie
