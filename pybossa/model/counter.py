# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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

from sqlalchemy import Integer
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP
from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp


class Counter(db.Model, DomainObject):
    '''A Counter lists the number of task runs for a given Task.'''

    __tablename__ = 'counter'

    #: Counter.ID
    id = Column(Integer, primary_key=True)
    #: UTC timestamp when the counter was created.
    created = Column(TIMESTAMP, default=make_timestamp)
    #: Project.ID that this counter is associated with.
    project_id = Column(Integer, ForeignKey('project.id',
                                            ondelete='CASCADE'),
                        nullable=False)
    #: Task.ID that this counter is associated with.
    task_id = Column(Integer, ForeignKey('task.id',
                                         ondelete='CASCADE'),
                     nullable=False)
    #: Number of task_runs for this task.
    n_task_runs = Column(Integer, default=0, nullable=False)
