# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
import json
from sqlalchemy.sql import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.base import _entity_descriptor
from pybossa.model.result import Result
from sqlalchemy import cast, Text
from pybossa.exc import WrongObjectError, DBIntegrityError


def generate_query_from_keywords(model, **kwargs):
    clauses = [_entity_descriptor(model, key) == value
                   for key, value in kwargs.items()
                   if key != 'info']
    if 'info' in kwargs.keys():
        info = json.dumps(kwargs['info'])
        clauses.append(cast(_entity_descriptor(model, 'info'), Text) == info)
    return and_(*clauses) if len(clauses) != 1 else (and_(*clauses), )


class ResultRepository(object):

    def __init__(self, db):
        self.db = db

    def get(self, id):
        return self.db.session.query(Result).get(id)

    def get_by(self, **attributes):
        return self.db.session.query(Result).filter_by(**attributes).first()

    def filter_by(self, limit=None, offset=0, yielded=False,
                  last_id=None, **filters):
        query_args = generate_query_from_keywords(Result, **filters)
        query = self.db.session.query(Result).filter(*query_args)
        if last_id:
            query = query.filter(Result.id > last_id)
            query = query.order_by(Result.id).limit(limit)
        else:
            query = query.order_by(Result.id).limit(limit).offset(offset)
        if yielded:
            limit = limit or 1
            return query.yield_per(limit)
        return query.all()

        #query = self.db.session.query(Result).filter_by(**filters)
        #query = query.order_by(Result.id).limit(limit).offset(offset)
        #return query.all()

    def update(self, result):
        self._validate_can_be('updated', result)
        try:
            self.db.session.merge(result)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def _validate_can_be(self, action, result):
        if not isinstance(result, Result):
            name = result.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
