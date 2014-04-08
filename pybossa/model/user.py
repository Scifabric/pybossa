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

from sqlalchemy import Integer, Boolean, Unicode, Text, String, BigInteger
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy import event
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp, JSONType, make_uuid




class User(db.Model, DomainObject, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)
    #: email address ...
    email_addr = Column(Unicode(length=254), unique=True, nullable=False)
    #: user name
    name = Column(Unicode(length=254), unique=True, nullable=False)
    #: full name
    fullname = Column(Unicode(length=500), nullable=False)
    #: locale
    locale = Column(Unicode(length=254), default=u'en', nullable=False)
    #: api key
    api_key = Column(String(length=36), default=make_uuid, unique=True)
    passwd_hash = Column(Unicode(length=254), unique=True)
    #: Admin flag Boolean Integer (0,1)
    admin = Column(Boolean, default=False)
    # Privacy mode flag
    privacy_mode = Column(Boolean, default=True, nullable=False)
    #: TODO: find out ... bossa specific
    category = Column(Integer)
    #: TODO: find out ...
    flags = Column(Integer)
    # Twitter user_id field
    twitter_user_id = Column(BigInteger, unique=True)
    # Facebook user_id field
    facebook_user_id = Column(BigInteger, unique=True)
    # Google user_id field
    google_user_id = Column(String, unique=True)
    # CKAN API key field
    ckan_api = Column(String, unique=True)
    #: arbitrary additional information about the user in a JSON dict.
    info = Column(JSONType, default=dict)

    def get_id(self):
        '''id for login system. equates to name'''
        return self.name

    def set_password(self, password):
        self.passwd_hash = generate_password_hash(password)

    def check_password(self, password):
        # OAuth users do not have a password
        if self.passwd_hash:
            return check_password_hash(self.passwd_hash, password)
        else:
            return False

    @classmethod
    def by_name(cls, name):
        '''Lookup user by (user)name.'''
        return db.session.query(User).filter_by(name=name).first()

    ## Relationships
    #: `Task`s for this user
    task_runs = relationship('TaskRun', backref='user')
    apps = relationship('App', backref='owner')
    blogposts = relationship('Blogpost', backref='owner')


@event.listens_for(User, 'before_insert')
def make_admin(mapper, conn, target):
    users = conn.scalar('select count(*) from "user"')
    if users == 0:
        target.admin = True
