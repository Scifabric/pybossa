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

from sqlalchemy import Integer, Unicode, UnicodeText, Text, Boolean
from sqlalchemy.schema import Column, ForeignKey

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.mutable import MutableDict

class Announcement(db.Model, DomainObject):
    """An Announcement"""

    __tablename__ = 'announcement'

    #: Announcement ID
    id = Column(Integer, primary_key=True)
    #: UTC timestamp when the announcement is created
    created = Column(Text, default=make_timestamp)
    #: User.ID for the Announcement
    user_id = Column(Integer, ForeignKey('user.id'))
    #: UTC timestamp when the blogpost is updated
    updated = Column(Text, default=make_timestamp)
    #: Title of the Announcement
    title = Column(Unicode(length=255), nullable=False)
    #: Body of the Announcement
    body = Column(UnicodeText, nullable=False)
    #: media_url Heading picture or cover for blogpost
    info = Column(MutableDict.as_mutable(JSON), default=dict())
    #: Media URL with cover photo for the blog post
    media_url = Column(Text)
    #: Published flag
    published = Column(Boolean, nullable=False, default=False)


    @classmethod
    def public_attributes(self):
        """Return a list of public attributes."""
        return ['created', 'updated', 'id', 'user_id',
                'title', 'body', 'media_url', 'published']

    @classmethod
    def public_info_keys(self):
        """Return a list of public info keys."""
        return []
