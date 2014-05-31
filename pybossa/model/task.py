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

from sqlalchemy import Integer, Boolean, Float, UnicodeText, Text
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.orm import relationship, backref

from pybossa.core import db
from pybossa.model import DomainObject, JSONType, make_timestamp
from pybossa.model.task_run import TaskRun




class Task(db.Model, DomainObject):
    '''An individual Task which can be performed by a user. A Task is
    associated to a project.
    '''
    __tablename__ = 'task'


    id = Column(Integer, primary_key=True)
    created = Column(Text, default=make_timestamp)
    app_id = Column(Integer, ForeignKey('app.id', ondelete='CASCADE'), nullable=False)
    state = Column(UnicodeText, default=u'ongoing')
    quorum = Column(Integer, default=0)
    calibration = Column(Integer, default=0)
    priority_0 = Column(Float, default=0)
    info = Column(JSONType, default=dict)
    n_answers = Column(Integer, default=30)

    task_runs = relationship(TaskRun, cascade='all, delete, delete-orphan', backref='task')


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
