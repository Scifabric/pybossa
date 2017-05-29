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

from sqlalchemy.exc import IntegrityError

from pybossa.repositories import Repository
from pybossa.model.announcement import Announcement
from pybossa.exc import WrongObjectError, DBIntegrityError


class AnnouncementRepository(Repository):

    def __init__(self, db):
        self.db = db

    def get(self, id):
        return self.db.session.query(Announcement).get(id)

    def get_all_announcements(self):
        return self.db.session.query(Announcement).all()

    def get_by(self, **attributes):
        return self.db.session.query(Announcement).filter_by(**attributes).first()

    def filter_by(self, limit=None, offset=0, yielded=False, last_id=None,
                  **filters):
        return self._filter_by(Announcement, limit, offset, yielded,
                               last_id, **filters)

    def save(self, announcement):
        self._validate_can_be('saved', announcement)
        try:
            self.db.session.add(announcement)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, announcement):
        self._validate_can_be('updated', announcement)
        try:
            self.db.session.merge(announcement)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete(self, announcement):
        self._validate_can_be('deleted', announcement)
        announcement = self.db.session.query(Announcement).filter(Announcement.id==announcement.id).first()
        self.db.session.delete(announcement)
        self.db.session.commit()

    def _validate_can_be(self, action, announcement):
        if not isinstance(announcement, Announcement):
            name = announcement.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
