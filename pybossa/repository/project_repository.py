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

from sqlalchemy import or_, func

from pybossa.core import db
from pybossa.model.app import App
from pybossa.model.featured import Featured



class ProjectRepository(object):


    def __init__(self, db):
        self.db = db


    def get(self, id):
        return self.db.session.query(App).get(id)

    def save(self, project):
        db.session.add(project)
        db.session.commit()
