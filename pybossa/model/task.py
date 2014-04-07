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

#import os
#from glob import iglob
import logging
import datetime
#import time
import json
import uuid

from werkzeug import generate_password_hash, check_password_hash
import flask.ext.login
from sqlalchemy import BigInteger, Integer, Boolean, Unicode,\
        Float, UnicodeText, Text, String
from sqlalchemy.schema import Table, MetaData, Column, ForeignKey
from sqlalchemy.orm import relationship, backref, class_mapper
from sqlalchemy.types import MutableType, TypeDecorator
from sqlalchemy import event, text
from sqlalchemy.engine import reflection
from sqlalchemy import create_engine
from sqlalchemy.schema import (
    MetaData,
    Table,
    DropTable,
    ForeignKeyConstraint,
    DropConstraint,
    )

from pybossa.core import db
from pybossa.util import pretty_date
from util import DomainObject, make_timestamp, JSONType




class Task(db.Model, DomainObject):
    '''An individual Task which can be performed by a user. A Task is
    associated to an App.
    '''
    __tablename__ = 'task'
    #: unique id (automatically generated)
    id = Column(Integer, primary_key=True)
    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)
    #: ForeignKey to App.id (NB: use task relationship rather than this field
    #: in normal use
    app_id = Column(Integer, ForeignKey('app.id', ondelete='CASCADE'), nullable=False)
    #: a StateEnum instance
    # TODO: state should be an integer?
    state = Column(UnicodeText, default=u'ongoing')
    #: Quorum (number of times this task should be done by different users)
    quorum = Column(Integer, default=0)
    #: Boolean indicating whether this is a calibration Task or not.
    calibration = Column(Integer, default=0)
    #: Value between 0 and 1 indicating priority of task within App
    #: (higher = more important)
    priority_0 = Column(Float, default=0)
    #: all configuration / details of the Task is stored in info which is
    #: an arbitrary JSON object. (Usually expected to be a hash/dict)
    #: For example for an image classification project this would be::
    #:
    #:    {
    #:       url: [image-url],
    #:       question: [is this a person]
    #:    }
    info = Column(JSONType, default=dict)
    #: Number of answers or TaskRuns per task
    n_answers = Column(Integer, default=30)

    ## Relationships
    #: `TaskRun`s for this task`
    task_runs = relationship('TaskRun', cascade='all, delete, delete-orphan', backref='task')

    def pct_status(self):
        """Returns the percentage of Tasks that are completed"""
        # DEPRECATED: self.info.n_answers will be removed
        # DEPRECATED: use self.t.n_answers instead
        if (self.info.get('n_answers')):
            self.n_answers = int(self.info['n_answers'])
        if self.n_answers != 0 and self.n_answers != None:
            return float(len(self.task_runs)) / self.n_answers
        else:  # pragma: no cover
            return float(0)
