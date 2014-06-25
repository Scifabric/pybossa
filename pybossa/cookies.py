# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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


class CookieHandler(object):
    def __init__(self, request, signer, expiration=1200):
        self.request = request
        self.signer = signer
        self.expiration = expiration

    def _create_or_update_cookie(self, project, user):
        cookie_name = '%spswd' % project.short_name
        cookie = request.cookies.get(cookie_name)
        cookie = signer.loads(cookie) if cookie else []
        cookie.append(get_user_id_or_ip())
        cookie = signer.dumps(cookie)
        return cookie

    def add_cookie_to(self, response, project, user):
        cookie_name = '%spswd' % project.short_name
        cookie = self._create_or_update_cookie(project, user)
        response.set_cookie(cookie_name, cookie, max_age=self.max_age)
        return response

    def get_cookie_from(self, project):
        cookie_name = '%spswd' % project.short_name
        signed_cookie = self.request.cookies.get(cookie_name)
        cookie = signer.loads(signed_cookie) if signed_cookie else []
        return cookie
