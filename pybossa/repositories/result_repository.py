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
from sqlalchemy import cast, Date
from pybossa.repositories import Repository
from pybossa.model.result import Result
from pybossa.exc import WrongObjectError, DBIntegrityError
from sqlalchemy import text


class ResultRepository(Repository):

    def get(self, id):
        return self.db.session.query(Result).get(id)

    def get_by(self, **attributes):
        if 'last_version' not in attributes.keys():
            attributes['last_version'] = True
        return self.db.session.query(Result).filter_by(**attributes).first()

    def filter_by(self, limit=None, offset=0, yielded=False,
                  last_id=None, fulltextsearch=None, desc=False, **filters):
        if 'last_version' not in filters.keys():
            filters['last_version'] = True
        if filters['last_version'] is False:
            filters.pop('last_version')

        return self._filter_by(Result, limit, offset,
                              yielded, last_id,
                              fulltextsearch,
                              desc, **filters)

    def update(self, result):
        self._validate_can_be('updated', result)
        try:
            self.db.session.merge(result)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete_results_from_project(self, project):
        sql = text('''
                   DELETE FROM result WHERE project_id=:project_id;
                   ''')
        self.db.session.execute(sql, dict(project_id=project.id))
        self.db.session.commit()


    def _validate_can_be(self, action, result):
        if not isinstance(result, Result):
            name = result.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
