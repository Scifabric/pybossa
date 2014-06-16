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

from sqlalchemy import Integer, Unicode, UnicodeText, Text
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy import event

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp, update_redis



class Blogpost(db.Model, DomainObject):
    """A blog post associated to a given app"""

    __tablename__ = 'blogpost'

    id = Column(Integer, primary_key=True)
    created = Column(Text, default=make_timestamp)
    app_id = Column(Integer, ForeignKey('app.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    title = Column(Unicode(length=255), nullable=False)
    body = Column(UnicodeText, nullable=False)


@event.listens_for(Blogpost, 'after_insert')
def add_event(mapper, conn, target):
    """Update PyBossa feed with new blog post."""
    sql_query = ('select name, short_name, info from app \
                 where id=%s') % target.app_id
    results = conn.execute(sql_query)
    obj = target.dictize()
    obj = dict(id=target.app_id,
               name=None,
               short_name=None,
               info=None,
               action_updated='Blog')
    for r in results:
        obj['name'] = r.name
        obj['short_name'] = r.short_name
        obj['info'] = r.info
    update_redis(obj)
