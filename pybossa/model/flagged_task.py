# -*- coding: utf8 -*-
# This file is part of myKaarma.
#
# 

from sqlalchemy import Integer, Text
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp



class FlaggedTask(db.Model, DomainObject):
    '''A run of a given task by a specific user.
    '''
    __tablename__ = 'flagged_task'

    #: ID of the FlaggedTask
    id = Column(Integer, primary_key=True)
    #: Project.id of the project associated with this FlaggedTask.
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    #: Task.id of the task associated with this FlaggedTask.
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False)
    #: User.id of the user contributing the FlaggedTask (only if authenticated)
    user_id = Column(Integer, ForeignKey('user.id'))
    #: User.ip of the user contributing the FlaggedTask (only if anonymous)
    user_ip = Column(Text)
    #: Reason for flagging
    reason = Column(Text)
    '''General writable field that should be used by clients to record results\
    of a FlaggedTask. Usually a template for this will be provided by Task
    For example::
        result: {
            whatever information should be recorded -- up to task presenter
        }
    '''
