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
from sqlalchemy.dialects.postgresql import JSON

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp
from pybossa.model.task_run import TaskRun


class Task(db.Model, DomainObject):
    '''An individual Task which can be performed by a user. A Task is
    associated to a project.
    '''
    __tablename__ = 'task'


    #: Task.ID
    id = Column(Integer, primary_key=True)
    #: UTC timestamp when the task was created.
    created = Column(Text, default=make_timestamp)
    #: Project.ID that this task is associated with.
    project_id = Column(Integer, ForeignKey('project.id', ondelete='CASCADE'), nullable=False)
    #: Task.state: ongoing or completed.
    state = Column(UnicodeText, default=u'ongoing')
    quorum = Column(Integer, default=0)
    #: If the task is a calibration task
    calibration = Column(Integer, default=0)
    #: Priority of the task from 0.0 to 1.0
    priority_0 = Column(Float, default=0)
    #: Task.info field in JSON with the data for the task.
    info = Column(JSON)
    #: Number of answers to collect for this task.
    n_answers = Column(Integer, default=30)

    task_runs = relationship(TaskRun, cascade='all, delete, delete-orphan', backref='task')


    def pct_status(self):
        """Returns the percentage of Tasks that are completed"""
        if self.n_answers != 0 and self.n_answers is not None:
            return float(len(self.task_runs)) / self.n_answers
        else:  # pragma: no cover
            return float(0)
