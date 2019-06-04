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

from sqlalchemy import Integer, Boolean, Float, UnicodeText, Text, DateTime
import sqlalchemy
from sqlalchemy.schema import Column, ForeignKey, Index
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.ext.mutable import MutableList
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
    #: Task.info field in JSONB with the data for the task.
    info = Column(JSONB)
    #: Number of answers to collect for this task.
    n_answers = Column(Integer, default=1)
    #: Array of User IDs that favorited this task
    fav_user_ids = Column(MutableList.as_mutable(ARRAY(Integer)))
    #: completed task can be marked as exported=True after its exported
    exported = Column(Boolean, default=False)
    #: Task.user_pref field in JSONB with user preference data for the task.
    user_pref = Column(JSONB)
    #: Task.gold_answers field in JSONB to record golden answers for fields under Task.info.
    gold_answers = Column(JSONB)
    #: Task.expiration field to determine when a task should no longer be scheduled. As UTC timestamp without timezone
    expiration = Column(DateTime, nullable=True)

    task_runs = relationship(TaskRun, cascade='all, delete, delete-orphan', backref='task')

    def pct_status(self):
        """Returns the percentage of Tasks that are completed"""
        if self.n_answers != 0 and self.n_answers is not None:
            return float(len(self.task_runs)) / self.n_answers
        else:  # pragma: no cover
            return float(0)

    __table_args__ = (
        Index('task_info_idx', sqlalchemy.text('md5(info::text)')),
    )

Index('task_project_id_idx', Task.project_id)
