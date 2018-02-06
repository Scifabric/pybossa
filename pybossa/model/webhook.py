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

from sqlalchemy import Integer, Text
from sqlalchemy.schema import Column, ForeignKey

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp
from sqlalchemy.dialects.postgresql import JSONB

class Webhook(db.Model, DomainObject):
    '''A Table with Categories for Projects.'''

    __tablename__ = 'webhook'

    #: Webook ID
    id = Column(Integer, primary_key=True)
    #: Webhook created (aka triggered)
    created = Column(Text, default=make_timestamp)
    #: Webhook updated
    updated = Column(Text, default=make_timestamp)
    #: Webhook project.id
    project_id = Column(Integer, ForeignKey('project.id', ondelete='CASCADE'),
                        nullable=False)
    #: Webhook payload
    payload = Column(JSONB)
    #: Webhook response
    response = Column(Text)
    #: Webhook response status code
    response_status_code = Column(Integer)
