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


class BlogpostAuth(object):

    def __init__(self, project_repo):
        self.project_repo = project_repo

    def can(self, user, action, blogpost=None, project_id=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, blogpost, project_id)

    def _create(self, user, blogpost=None, project_id=None):
        if user.is_anonymous() or (blogpost is None and project_id is None):
            return False
        project = self._get_project(blogpost, project_id)
        if blogpost is None:
            return project.owner_id == user.id
        return blogpost.user_id == project.owner_id == user.id

    def _read(self, user, blogpost=None, project_id=None):
        project = self._get_project(blogpost, project_id)
        if project and not project.hidden:
            return True
        if user.is_anonymous() or (blogpost is None and project_id is None):
            return False
        return user.admin or user.id == project.owner_id

    def _update(self, user, blogpost, project_id=None):
        if user.is_anonymous():
            return False
        return blogpost.user_id == user.id

    def _delete(self, user, blogpost, project_id=None):
        if user.is_anonymous():
            return False
        return user.admin or blogpost.user_id == user.id

    def _get_project(self, blogpost, project_id):
        if blogpost is not None:
            return self.project_repo.get(blogpost.project_id)
        return self.project_repo.get(project_id)
