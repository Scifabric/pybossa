# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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
from pybossa.model.helpingmaterial import HelpingMaterial
from pybossa.exc import WrongObjectError, DBIntegrityError


class HelpingMaterialRepository(Repository):

    def get(self, id):
        return self.db.session.query(HelpingMaterial).get(id)

    def get_by(self, **attributes):
        return self.db.session.query(HelpingMaterial).filter_by(**attributes).first()

    def filter_by(self, limit=None, offset=0, yielded=False,
                  last_id=None, fulltextsearch=None, desc=False, **filters):
        return self._filter_by(HelpingMaterial, limit, offset, yielded,
                               last_id, fulltextsearch, desc, **filters)

    def save(self, hm):
        self._validate_can_be('saved', hm)
        try:
            self.db.session.add(hm)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, hm):
        self._validate_can_be('updated', hm)
        try:
            self.db.session.merge(hm)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete(self, hm):
        self._validate_can_be('deleted', hm)
        blog = self.db.session.query(HelpingMaterial).filter(HelpingMaterial.id==hm.id).first()
        self.db.session.delete(blog)
        self.db.session.commit()

    def _validate_can_be(self, action, hm):
        if not isinstance(hm, HelpingMaterial):
            name = hm.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
