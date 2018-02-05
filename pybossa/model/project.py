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

from sqlalchemy import Integer, Boolean, Unicode, Float, UnicodeText, Text
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.ext.mutable import MutableDict, MutableList
from flask import current_app

from pybossa.core import db, signer
from pybossa.model import DomainObject, make_timestamp, make_uuid
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.category import Category
from pybossa.model.blogpost import Blogpost


class Project(db.Model, DomainObject):
    '''A microtasking Project to which Tasks are associated.
    '''

    __tablename__ = 'project'

    #: ID of the project
    id = Column(Integer, primary_key=True)
    #: UTC timestamp when the project is created
    created = Column(Text, default=make_timestamp)
    #: UTC timestamp when the project is updated (or any of its relationships)
    updated = Column(Text, default=make_timestamp, onupdate=make_timestamp)
    #: Project name
    name = Column(Unicode(length=255), unique=True, nullable=False)
    #: Project slug for the URL
    short_name = Column(Unicode(length=255), unique=True, nullable=False)
    #: Project description
    description = Column(Unicode(length=255), nullable=False)
    #: Project long description
    long_description = Column(UnicodeText)
    #: Project webhook
    webhook = Column(Text)
    #: If the project allows anonymous contributions
    allow_anonymous_contributors = Column(Boolean, default=True)
    #: If the project is published
    published = Column(Boolean, nullable=False, default=False)
    # If the project is featured
    featured = Column(Boolean, nullable=False, default=False)
    # Secret key for project
    secret_key = Column(Text, default=make_uuid)
    # Zip download
    zip_download = Column(Boolean, default=True)
    # If the project owner has been emailed
    contacted = Column(Boolean, nullable=False, default=False)
    #: Project owner_id
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    #: Project Category
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    #: Project info field formatted as JSON
    info = Column(MutableDict.as_mutable(JSONB), default=dict())

    tasks = relationship(Task, cascade='all, delete, delete-orphan', backref='project')
    task_runs = relationship(TaskRun, backref='project',
                             cascade='all, delete-orphan',
                             order_by='TaskRun.finish_time.desc()')
    category = relationship(Category)
    blogposts = relationship(Blogpost, cascade='all, delete-orphan', backref='project')
    owners_ids = Column(MutableList.as_mutable(ARRAY(Integer)), default=list())

    def needs_password(self):
        return self.get_passwd_hash() is not None

    def get_passwd_hash(self):
        return self.info.get('passwd_hash')

    def get_passwd(self):
        if self.needs_password():
            return signer.loads(self.get_passwd_hash())
        return None

    def set_password(self, password):
        if len(password) > 1:
            self.info['passwd_hash'] = signer.dumps(password)
            return True
        self.info['passwd_hash'] = None
        return False

    def check_password(self, password):
        if self.needs_password():
            return self.get_passwd() == password
        return False

    def has_autoimporter(self):
        return self.get_autoimporter() is not None

    def get_autoimporter(self):
        return self.info.get('autoimporter')

    def set_autoimporter(self, new=None):
        self.info['autoimporter'] = new

    def delete_autoimporter(self):
        del self.info['autoimporter']

    def has_presenter(self):
        if current_app.config.get('DISABLE_TASK_PRESENTER') is True:
            return True
        else:
            return self.info.get('task_presenter') not in ('', None)

    @classmethod
    def public_attributes(self):
        """Return a list of public attributes."""
        return ['id', 'description', 'info', 'n_tasks', 'n_volunteers', 'name',
                'overall_progress', 'short_name', 'created', 'category_id',
                'long_description', 'last_activity', 'last_activity_raw',
                'n_task_runs', 'n_results', 'owner', 'updated', 'featured',
                'owner_id', 'n_completed_tasks', 'n_blogposts', 'owners_ids']

    @classmethod
    def public_info_keys(self):
        """Return a list of public info keys."""
        default = ['container', 'thumbnail', 'thumbnail_url',
                   'task_presenter', 'tutorial', 'sched']
        extra = current_app.config.get('PROJECT_INFO_PUBLIC_FIELDS')
        if extra:
            return list(set(default).union(set(extra)))
        else:
            return default
