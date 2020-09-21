# -*- coding: utf8 -*-
# This file is part of myKaarma.
#
# 

from sqlalchemy import Integer, Text
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from pybossa.core import db
from pybossa.model import DomainObject, make_timestamp



class UserAuthorities(db.Model, DomainObject):
    '''A run of a given task by a specific user.
    '''
    __tablename__ = 'user_authorities'

    #: ID of the UserAuthority
    id = Column(Integer, primary_key=True)
    #: Resource.id of the resource associated with this UserAuthority
    resource_id = Column(Integer)
    #: User.id of the user contributing the UserAuthority 
    user_id = Column(Integer, ForeignKey('user.id'))
    #: Resource Type of the operation contributing the UserAuthority 
    resource_type = Column(Text)
    #: Operation of the operation contributing the UserAuthority 
    operation = Column(Text)
   
    '''General writable field that should be used by clients to record results\
    of a UserAuthority. Usually a template for this will be provided by Task
    For example::
        result: {
            whatever information should be recorded -- up to task presenter
        }
    '''
