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


from pybossa.core import db
from pybossa.model import DomainObject, JSONType, make_timestamp
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.featured import Featured
from pybossa.model.category import Category
from pybossa.model.blogpost import Blogpost



class App(db.Model, DomainObject):
    '''A microtasking Project to which Tasks are associated.
    '''

    __tablename__ = 'app'

    id = Column(Integer, primary_key=True)
    created = Column(Text, default=make_timestamp)
    name = Column(Unicode(length=255), unique=True, nullable=False)
    short_name = Column(Unicode(length=255), unique=True, nullable=False)
    description = Column(Unicode(length=255), nullable=False)
    long_description = Column(UnicodeText)
    allow_anonymous_contributors = Column(Boolean, default=True)
    long_tasks = Column(Integer, default=0)
    hidden = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    time_estimate = Column(Integer, default=0)
    time_limit = Column(Integer, default=0)
    calibration_frac = Column(Float, default=0)
    bolt_course_id = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey('category.id'))
    info = Column(JSONType, default=dict)


    tasks = relationship(Task, cascade='all, delete, delete-orphan', backref='app')
    task_runs = relationship(TaskRun, backref='app',
                             cascade='all, delete-orphan',
                             order_by='TaskRun.finish_time.desc()')
    featured = relationship(Featured, cascade='all, delete, delete-orphan', backref='app')
    category = relationship(Category)
    blogposts = relationship(Blogpost, cascade='all, delete-orphan', backref='app')


@event.listens_for(App, 'before_update')
@event.listens_for(App, 'before_insert')
def empty_string_to_none(mapper, conn, target):
    if target.name == '':
        target.name = None
    if target.short_name == '':
        target.short_name = None
    if target.description == '':
        target.description = None
