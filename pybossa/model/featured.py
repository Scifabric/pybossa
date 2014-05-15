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

from sqlalchemy import Integer, Text
from sqlalchemy.schema import Column, ForeignKey

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp



class Featured(db.Model, DomainObject):
    '''A Table with Featured Projects.'''

    __tablename__ = 'featured'

    id = Column(Integer, primary_key=True)
    created = Column(Text, default=make_timestamp)
    app_id = Column(Integer, ForeignKey('app.id'))
