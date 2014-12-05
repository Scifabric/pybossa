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

from flask.ext.login import current_user

from pybossa.core import project_repo


def create(_auditlog):
    return False


def read(_auditlog=None, _app_id=None):
    app = _get_app(_auditlog, _app_id)
    if current_user.is_anonymous() or (_auditlog is None and _app_id is None):
        return False
    return current_user.admin or (current_user.id == app.owner_id
                                  and current_user.pro)


def update(_auditlog):
    return False


def delete(_auditlog):
    return False


def _get_app(_auditlog, _app_id):
    if _auditlog is not None:
        return project_repo.get(_auditlog.app_id)
    return project_repo.get(_app_id)
