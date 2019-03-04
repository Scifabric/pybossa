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

from sqlalchemy import Integer, Text, Index
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp



class TaskRun(db.Model, DomainObject):
    '''A run of a given task by a specific user.
    '''
    __tablename__ = 'task_run'

    #: ID of the TaskRun
    id = Column(Integer, primary_key=True)
    #: UTC timestamp for when TaskRun is delivered to user.
    created = Column(Text, default=make_timestamp)
    #: Project.id of the project associated with this TaskRun.
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    #: Task.id of the task associated with this TaskRun.
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False)
    #: User.id of the user contributing the TaskRun (only if authenticated)
    user_id = Column(Integer, ForeignKey('user.id'))
    #: User.ip of the user contributing the TaskRun (only if anonymous)
    user_ip = Column(Text)
    #: UTC timestamp for when TaskRun is saved to DB.
    finish_time = Column(Text, default=make_timestamp)
    timeout = Column(Integer)
    calibration = Column(Integer)
    #: External User ID
    external_uid = Column(Text)
    #: Media URL to an Image, Audio, PDF, or Video
    media_url = Column(Text)
    #: Value of the answer.
    info = Column(JSONB)
    '''General writable field that should be used by clients to record results\
    of a TaskRun. Usually a template for this will be provided by Task
    For example::
        result: {
            whatever information should be recorded -- up to task presenter
        }
    '''

Index('task_run_task_id_idx', TaskRun.task_id)
Index('task_run_user_id_idx', TaskRun.user_id)
Index('task_run_project_id_idx', TaskRun.project_id)
Index('unique_user_id_task_id_idx', TaskRun.task_id, TaskRun.user_id, TaskRun.user_ip, TaskRun.external_uid, unique=True)
