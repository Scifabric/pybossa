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

from sqlalchemy import Integer, Boolean, Unicode, Text, String, BigInteger, Date
from sqlalchemy.schema import Column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from flask_login import UserMixin
from flask import current_app

from pybossa.core import db, signer
from pybossa.model import DomainObject, make_timestamp, make_uuid
from pybossa.model.project import Project
from pybossa.model.task_run import TaskRun
from pybossa.model.blogpost import Blogpost


class User(db.Model, DomainObject, UserMixin):
    '''A registered user of the PYBOSSA system'''

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    #: UTC timestamp of the user when it's created.
    created = Column(Text, default=make_timestamp)
    email_addr = Column(Unicode(length=254), unique=True, nullable=False)
    #: Name of the user (this is used as the nickname).
    name = Column(Unicode(length=254), unique=True, nullable=False)
    #: Fullname of the user.
    fullname = Column(Unicode(length=500), nullable=False)
    #: Language used by the user in the PYBOSSA server.
    locale = Column(Unicode(length=254), default='en', nullable=False)
    api_key = Column(String(length=36), default=make_uuid, unique=True)
    passwd_hash = Column(Unicode(length=254), unique=True)
    ldap = Column(Unicode, unique=True)
    admin = Column(Boolean, default=False)
    pro = Column(Boolean, default=False)
    privacy_mode = Column(Boolean, default=True, nullable=False)
    restrict = Column(Boolean, default=False, nullable=False)
    category = Column(Integer)
    flags = Column(Integer)
    twitter_user_id = Column(BigInteger, unique=True)
    facebook_user_id = Column(BigInteger, unique=True)
    google_user_id = Column(String, unique=True)
    ckan_api = Column(String, unique=True)
    newsletter_prompted = Column(Boolean, default=False)
    valid_email = Column(Boolean, default=False)
    confirmation_email_sent = Column(Boolean, default=False)
    subscribed = Column(Boolean, default=False)
    consent = Column(Boolean, default=False)
    info = Column(MutableDict.as_mutable(JSONB), default=dict())
    user_pref = Column(JSONB)
    notified_at = Column(Date, default=None)

    ## Relationships
    task_runs = relationship(TaskRun, backref='user')
    projects = relationship(Project, backref='owner')
    blogposts = relationship(Blogpost, backref='owner')


    def get_id(self):
        '''id for login system. equates to name'''
        return self.name


    def set_password(self, password):
        self.passwd_hash = signer.generate_password_hash(password)


    def check_password(self, password):
        # OAuth users do not have a password
        if self.passwd_hash:
            return signer.check_password_hash(self.passwd_hash, password)
        return False

    @classmethod
    def public_attributes(self):
        """Return a list of public attributes."""
        return ['created', 'name', 'fullname', 'info',
                'n_answers', 'registered_ago', 'rank', 'score', 'locale']

    @classmethod
    def public_info_keys(self):
        """Return a list of public info keys."""
        default = ['avatar', 'container', 'extra', 'avatar_url']
        extra = current_app.config.get('USER_INFO_PUBLIC_FIELDS')
        if extra:
            return list(set(default).union(set(extra)))
        else:
            return default
