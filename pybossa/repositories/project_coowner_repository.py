# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2017 SciFabric LTD.
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

from sqlalchemy.exc import IntegrityError

from pybossa.model.project_coowner import ProjectCoowner
from pybossa.exc import WrongObjectError, DBIntegrityError


class ProjectCoownerRepository(object):

    def __init__(self, db):
        self.db = db

    def get(self, id):
        """There are no project_coowner_id's."""
        pass

    def get_by(self, **attributes):
        return self.db.session.query(ProjectCoowner).filter_by(**attributes).first()

    def get_all(self):
        return self.db.session.query(ProjectCoowner).all()

    def filter_by(self, limit=None, offset=0, yielded=False, fulltextsearch=None, desc=False, **filters):
        # Remove owner_id from filters
        # it's just used for authentication
        for attr in ['owner_id', 'orderby']:
            if filters.get(attr):
                del filters[attr]
        query = self.db.session.query(ProjectCoowner).filter_by(**filters)
        query = query.order_by(ProjectCoowner.project_id).limit(limit).offset(offset)
        if yielded:
            limit = limit or 1
            return query.yield_per(limit)
        return query.all()

    def save(self, projectcoowner):
        self._validate_can_be('saved', projectcoowner)
        try:
            self.db.session.add(projectcoowner)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, projectcoowner):
        self._validate_can_be('updated', projectcoowner)
        try:
            self.db.session.merge(projectcoowner)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def _validate_can_be(self, action, projectcoowner):
        if not isinstance(projectcoowner, ProjectCoowner):
            name = projectcoowner.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
