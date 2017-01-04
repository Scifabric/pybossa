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


class Auditlog(db.Model, DomainObject):
    '''A Table with Audit logs for Projects.'''

    __tablename__ = 'auditlog'

    #: Audit log ID
    id = Column(Integer, primary_key=True)
    #: Project.id
    project_id = Column(Integer, nullable=False)
    #: Short name of the project
    project_short_name = Column(Text, nullable=False)
    #: User.id that took the action
    user_id = Column(Integer, nullable=False)
    #: Nickname of the user
    user_name = Column(Text, nullable=False)
    #: UTC timestamp when the Category was created
    created = Column(Text, default=make_timestamp, nullable=False)
    #: Action taken
    action = Column(Text, nullable=False)
    #: Caller: which process initiated the action: API or WEB
    caller = Column(Text, nullable=False)
    #: Attribute: which attribute has been updated
    attribute = Column(Text, nullable=False)
    #: Old_value
    old_value = Column(Text)
    #: New_value
    new_value = Column(Text)
