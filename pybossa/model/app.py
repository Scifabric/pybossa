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

from sqlalchemy import Integer, Boolean, Unicode, Float, UnicodeText, Text
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy import event


from pybossa.core import db, signer
from pybossa.model import DomainObject, JSONType, make_timestamp, update_redis
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.featured import Featured
from pybossa.model.category import Category
from pybossa.model.blogpost import Blogpost


class App(db.Model, DomainObject):
    '''A microtasking Project to which Tasks are associated.
    '''

    __tablename__ = 'app'

    #: ID of the project
    id = Column(Integer, primary_key=True)
    #: UTC timestamp when the project is created
    created = Column(Text, default=make_timestamp)
    #: Project name
    name = Column(Unicode(length=255), unique=True, nullable=False)
    #: Project slug for the URL
    short_name = Column(Unicode(length=255), unique=True, nullable=False)
    #: Project description
    description = Column(Unicode(length=255), nullable=False)
    #: Project long description
    long_description = Column(UnicodeText)
    #: If the project allows anonymous contributions
    allow_anonymous_contributors = Column(Boolean, default=True)
    long_tasks = Column(Integer, default=0)
    #: If the project is hidden
    hidden = Column(Integer, default=0)
    #: Project owner_id
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    time_estimate = Column(Integer, default=0)
    time_limit = Column(Integer, default=0)
    calibration_frac = Column(Float, default=0)
    bolt_course_id = Column(Integer, default=0)
    #: Project Category
    category_id = Column(Integer, ForeignKey('category.id'))
    #: Project info field formatted as JSON
    info = Column(JSONType, default=dict)


    tasks = relationship(Task, cascade='all, delete, delete-orphan', backref='app')
    task_runs = relationship(TaskRun, backref='app',
                             cascade='all, delete-orphan',
                             order_by='TaskRun.finish_time.desc()')
    featured = relationship(Featured, cascade='all, delete, delete-orphan', backref='app')
    category = relationship(Category)
    blogposts = relationship(Blogpost, cascade='all, delete-orphan', backref='app')



    def needs_password(self):
        return self.get_passwd_hash() is not None


    def get_passwd_hash(self):
        return self.info.get('passwd_hash')


    def get_passwd(self):
        if self.needs_password():
            return signer.loads(self.get_passwd_hash())
        return None


    def set_password(self, password):
        if len(password) > 1:
            self.info['passwd_hash'] = signer.dumps(password)
            return True
        self.info['passwd_hash'] = None
        return False


    def check_password(self, password):
        if self.needs_password():
            return self.get_passwd() == password
        return False


@event.listens_for(App, 'before_update')
@event.listens_for(App, 'before_insert')
def empty_string_to_none(mapper, conn, target):
    if target.name == '':
        target.name = None
    if target.short_name == '':
        target.short_name = None
    if target.description == '':
        target.description = None

@event.listens_for(App, 'after_insert')
def add_event(mapper, conn, target):
    """Update PyBossa feed with new app."""
    obj = dict(id=target.id,
               name=target.name,
               short_name=target.short_name,
               action_updated='Project')
    update_redis(obj)
