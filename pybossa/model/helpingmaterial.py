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

from sqlalchemy import Integer, Text, Float
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSONB
from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp
from sqlalchemy.ext.mutable import MutableDict


class HelpingMaterial(db.Model, DomainObject):
    '''A Helping Materials objects to give support/tutorials to users.'''

    __tablename__ = 'helpingmaterial'

    #: Counter.ID
    id = Column(Integer, primary_key=True)
    #: UTC timestamp when the counter was created.
    created = Column(TIMESTAMP, default=make_timestamp)
    #: Project.ID that this counter is associated with.
    project_id = Column(Integer, ForeignKey('project.id',
                                            ondelete='CASCADE'),
                        nullable=False)
    #: Info field where it can be stored anything related to it
    info = Column(MutableDict.as_mutable(JSONB), default=dict())
    media_url = Column(Text)
    #: Priority of the helping material from 0.0 to 1.0
    priority = Column(Float, default=0)

    @classmethod
    def public_attributes(self):
        """Return a list of public attributes."""
        return ['created', 'id', 'info', 'media_url', 'priority']

    @classmethod
    def public_info_keys(self):
        """Return a list of public info keys."""
        pass
