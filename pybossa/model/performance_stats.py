# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2019 Scifabric LTD.
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
import enum

from sqlalchemy import Integer, Text, Enum
from sqlalchemy.schema import Column, ForeignKey

from pybossa.core import db
from pybossa.model import DomainObject
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict


class StatType(str, enum.Enum):
    confusion_matrix = 'confusion_matrix'
    accuracy = 'accuracy'


class PerformanceStats(db.Model, DomainObject):
    '''A Table with Performance Stats for Users.'''

    __tablename__ = 'performance_stats'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id', ondelete='CASCADE'),
                        nullable=False)
    field = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user_key = Column(Text)
    stat_type = Column(Enum(StatType), nullable=False)
    info = Column(MutableDict.as_mutable(JSONB), default=dict())
