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

from sqlalchemy import Integer, Unicode, UnicodeText, Text
from sqlalchemy.schema import Column, ForeignKey

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp


class Announcement(db.Model, DomainObject):
    """An Announcement"""

    __tablename__ = 'announcement'

    #: Announcement ID
    id = Column(Integer, primary_key=True)
    #: UTC timestamp when the announcement is created
    created = Column(Text, default=make_timestamp)
    #: User.ID for the Announcement
    user_id = Column(Integer, ForeignKey('user.id'))
    #: Title of the Announcement
    title = Column(Unicode(length=255), nullable=False)
    #: Body of the Announcement
    body = Column(UnicodeText, nullable=False)

    @classmethod
    def public_attributes(self):
        """Return a list of public attributes."""
        return ['created', 'id', 'user_id',
                'title', 'body']

    @classmethod
    def public_info_keys(self):
        """Return a list of public info keys."""
        return []
