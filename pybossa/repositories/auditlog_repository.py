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
from pybossa.model.auditlog import Auditlog
from pybossa.exc import WrongObjectError, DBIntegrityError


class AuditlogRepository(Repository):

    def __init__(self, db):
        self.db = db

    def get(self, id):
        return self.db.session.query(Auditlog).get(id)

    def get_by(self, **attributes):
        return self.db.session.query(Auditlog).filter_by(**attributes).first()

    def filter_by(self, limit=None, offset=0, **filters):
        return self._filter_by(Auditlog, limit, offset, **filters)

    def save(self, auditlog):
        self._validate_can_be('saved', auditlog)
        try:
            self.db.session.add(auditlog)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def _validate_can_be(self, action, auditlog):
        if not isinstance(auditlog, Auditlog):
            name = auditlog.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
