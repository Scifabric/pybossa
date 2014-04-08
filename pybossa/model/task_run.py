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

from sqlalchemy import Integer, Text
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy import event

from pybossa.core import db
from pybossa.model import DomainObject, JSONType, make_timestamp




class TaskRun(db.Model, DomainObject):
    '''A run of a given task by a specific user.
    '''
    __tablename__ = 'task_run'
    #: id
    id = Column(Integer, primary_key=True)
    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)
    #: application id of this task run
    app_id = Column(Integer, ForeignKey('app.id'), nullable=False)
    #: task id of this task run
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False)
    #: user id of performer of this task
    user_id = Column(Integer, ForeignKey('user.id'))
    # ip address of this user (only if anonymous)
    user_ip = Column(Text)
    #: finish time (iso8601 formatted string)
    finish_time = Column(Text, default=make_timestamp)

    #: timeout for task
    timeout = Column(Integer)
    #: See same attribute in Task
    calibration = Column(Integer)
    info = Column(JSONType, default=dict)
    '''General writable field that should be used by clients to record results\
    of a TaskRun. Usually a template for this will be provided by Task
    For example::
        result: {
            whatever information shoudl be recorded -- up to task presenter
        }
    '''


@event.listens_for(TaskRun, 'after_insert')
def update_task_state(mapper, conn, target):
    """Update the task.state when n_answers condition is met."""
    sql_query = ('select count(id) from task_run \
                 where task_run.task_id=%s') % target.task_id
    n_answers = conn.scalar(sql_query)
    sql_query = ('select n_answers from task \
                 where task.id=%s') % target.task_id
    task_n_answers = conn.scalar(sql_query)
    if (n_answers) >= task_n_answers:
        sql_query = ("UPDATE task SET state=\'completed\' \
                     where id=%s") % target.task_id
        conn.execute(sql_query)