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
from flask.ext.login import UserMixin

from pybossa.core import db, signer
from pybossa.model import DomainObject, make_timestamp, JSONEncodedDict, make_uuid, update_redis
from pybossa.model.app import App
from pybossa.model.task_run import TaskRun
from pybossa.model.blogpost import Blogpost




class User(db.Model, DomainObject, UserMixin):
    '''A registered user of the PyBossa system'''

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    #: UTC timestamp of the user when it's created.
    created = Column(Text, default=make_timestamp)
    email_addr = Column(Unicode(length=254), unique=True, nullable=False)
    #: Name of the user (this is used as the nickname).
    name = Column(Unicode(length=254), unique=True, nullable=False)
    #: Fullname of the user.
    fullname = Column(Unicode(length=500), nullable=False)
    #: Language used by the user in the PyBossa server.
    locale = Column(Unicode(length=254), default=u'en', nullable=False)
    api_key = Column(String(length=36), default=make_uuid, unique=True)
    passwd_hash = Column(Unicode(length=254), unique=True)
    admin = Column(Boolean, default=False)
    pro = Column(Boolean, default=False)
    privacy_mode = Column(Boolean, default=True, nullable=False)
    category = Column(Integer)
    flags = Column(Integer)
    twitter_user_id = Column(BigInteger, unique=True)
    facebook_user_id = Column(BigInteger, unique=True)
    google_user_id = Column(String, unique=True)
    ckan_api = Column(String, unique=True)
    info = Column(JSONEncodedDict, default=dict)

    ## Relationships
    task_runs = relationship(TaskRun, backref='user')
    apps = relationship(App, backref='owner')
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
    def by_name(cls, name):
        '''Lookup user by (user)name.'''
        return db.session.query(User).filter_by(name=name).first()


@event.listens_for(User, 'before_insert')
def make_admin(mapper, conn, target):
    users = conn.scalar('select count(*) from "user"')
    if users == 0:
        target.admin = True


@event.listens_for(User, 'after_insert')
def add_event(mapper, conn, target):
    """Update PyBossa feed with new user."""
    obj = target.dictize()
    obj['action_updated']='User'
    update_redis(obj)
