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

from sqlalchemy import Integer, Text, Float
from sqlalchemy.schema import Column, ForeignKey

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict


class ProjectStats(db.Model, DomainObject):
    '''A Table with Project Stats for Projects.'''

    __tablename__ = 'project_stats'

    #: ID
    id = Column(Integer, primary_key=True)
    #: Project ID
    project_id = Column(Integer, ForeignKey('project.id', ondelete='CASCADE'),
                        nullable=False)
    #: Number of tasks
    n_tasks = Column(Integer, default=0)
    #: Number of task runs
    n_task_runs = Column(Integer, default=0)
    #: Number of results
    n_results = Column(Integer, default=0)
    #: Number of volunteers
    n_volunteers = Column(Integer, default=0)
    #: Number of completed tasks
    n_completed_tasks = Column(Integer, default=0)
    #: Overall progress
    overall_progress = Column(Integer, default=0)
    #: Average time to complete a task
    average_time = Column(Float, default=0)
    #: Number of blog posts
    n_blogposts = Column(Integer, default=0)
    #: Last Activity
    last_activity = Column(Text, default=make_timestamp)
    #: Stats payload
    info = Column(MutableDict.as_mutable(JSONB), default=dict())
