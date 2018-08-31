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

from sqlalchemy import Integer, Text, Boolean
from sqlalchemy.schema import Column, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import ARRAY

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp


class Result(db.Model, DomainObject):

    """A result associated for a task and its task runs."""

    __tablename__ = 'result'

    #: ID of the Result
    id = Column(Integer, primary_key=True)
    #: UTC timestamp for when a Result is created.
    created = Column(Text, default=make_timestamp)
    #: Project.id of the project associated with this Result.
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    #: Task.id of the task associated with this Result.
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False)
    #: Array of task_run ids associated with the result
    task_run_ids = Column(ARRAY(Integer), nullable=False)
    #: Last version
    last_version = Column(Boolean, default=True)
    #: Value of the Result.
    info = Column(JSONB)


Index('result_project_id_idx', Result.project_id)
Index('result_task_id_idx', Result.task_id)
