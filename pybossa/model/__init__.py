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

import datetime
import json
import uuid

from sqlalchemy import Text
from sqlalchemy.orm import relationship, backref, class_mapper
from sqlalchemy.types import MutableType, TypeDecorator
from sqlalchemy import event
from sqlalchemy.engine import reflection
from sqlalchemy.schema import (
    MetaData,
    Table,
    DropTable,
    ForeignKeyConstraint,
    DropConstraint,
    )

import logging
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

log = logging.getLogger(__name__)



class DomainObject(object):

    def dictize(self):
        out = {}
        for col in self.__table__.c:
            out[col.name] = getattr(self, col.name)
        return out

    @classmethod
    def undictize(cls, dict_):
        raise NotImplementedError()

    def __str__(self):  # pragma: no cover
        return self.__unicode__().encode('utf8')

    def __unicode__(self): # pragma: no cover
        repr = u'<%s' % self.__class__.__name__
        table = class_mapper(self.__class__).mapped_table
        for col in table.c:
            try:
                repr += u' %s=%s' % (col.name, getattr(self, col.name))
            except Exception, inst:
                repr += u' %s=%s' % (col.name, inst)

        repr += '>'
        return repr



class JSONType(MutableType, TypeDecorator):
    '''Additional Database Type for handling JSON values.
    '''
    impl = Text

    def __init__(self):
        super(JSONType, self).__init__()

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialiect):
        return json.loads(value)

    def copy_value(self, value):
        return json.loads(json.dumps(value))




def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()


def make_uuid():
    return str(uuid.uuid4())


def rebuild_db():
    # See this SQLAlchemy recipe: http://www.sqlalchemy.org/trac/wiki/UsageRecipes/DropEverything
    inspector = reflection.Inspector.from_engine(db.engine)
    # gather all data first before dropping anything.
    # some DBs lock after things have been dropped in
    # a transaction.

    metadata = MetaData()

    tbs = []
    all_fks = []

    for table_name in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if not fk['name']: # pragma: no cover
                continue
            fks.append(
                ForeignKeyConstraint((),(),name=fk['name'])
                )
        t = Table(table_name,metadata,*fks)
        tbs.append(t)
        all_fks.extend(fks)

    for fkc in all_fks:
        db.engine.execute(DropConstraint(fkc))

    for table in tbs:
        db.engine.execute(DropTable(table))

    db.session.commit()
    db.create_all()
