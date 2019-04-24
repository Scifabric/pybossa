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
"""Module for password protect a project."""
from flask_login import current_user


class ProjectPasswdManager(object):

    """Class to create a Password Manager for projects."""

    def __init__(self, cookie_handler):
        """Init method."""
        self.cookie_handler = cookie_handler

    def password_needed(self, project, user_id_or_ip):
        """Check if password is required."""
        if project.needs_password() and (current_user.is_anonymous or not
                                         (current_user.admin or current_user.subadmin or
                                          current_user.id in project.owners_ids)):
            cookie = self.cookie_handler.get_cookie_from(project)
            request_passwd = user_id_or_ip not in cookie
            return request_passwd
        return False

    def validates(self, password, project):
        """Validate password for project."""
        return project.check_password(password)

    def update_response(self, response, project, user):
        """Update response."""
        return self.cookie_handler.add_cookie_to(response, project, user)
