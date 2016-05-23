# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
# Cache global variables for timeouts

""" This package exports repository objects.

These objects are an abstraction layer between the ORM and the application:

    * user_repo
    * project_repo
    * blog_repo
    * task_repo
    * auditlog_repo
    * webhook_repo
    * result_repo

The responsibility of these repositories is only fetching one or many objects of
a kind and/or saving them to the DB by calling the ORM apropriate methods.

For more complex DB queries, refer to other packages or services within
PyBossa.
"""
import json
from pybossa.model.project import Project
from sqlalchemy.sql import and_
from sqlalchemy import cast, Text, func
from sqlalchemy.orm.base import _entity_descriptor

class Repository(object):

    def __init__(self, db):
        self.db = db

    def generate_query_from_keywords(self, model, fulltextsearch=None, **kwargs):
        clauses = [_entity_descriptor(model, key) == value
                       for key, value in kwargs.items()
                       if key != 'info']
        if 'info' in kwargs.keys():
            clauses = clauses + self.handle_info_json(model, kwargs['info'],
                                                      fulltextsearch)
        return and_(*clauses) if len(clauses) != 1 else (and_(*clauses), )


    def handle_info_json(self, model, info, fulltextsearch=None):
        """Handle info JSON query filter."""
        clauses = []
        if '::' in info:
            pairs = info.split('|')
            for pair in pairs:
                if pair != '':
                    k,v = pair.split("::")
                    if fulltextsearch == '1':
                        vector = _entity_descriptor(model, 'info')[k].astext
                        clause = func.to_tsvector(vector).match(v)
                        clauses.append(clause)
                    else:
                        clauses.append(_entity_descriptor(model,
                                                          'info')[k].astext == v)
        else:
            info = json.dumps(info)
            clauses.append(cast(_entity_descriptor(model, 'info'),
                                Text) == info)
        return clauses


    def create_context(self, filters, fulltextsearch, model):
        """Return query with context aware query."""
        owner_id = None
        query = None

        if filters.get('owner_id'):
            owner_id = filters.get('owner_id')
            del filters['owner_id']
        query_args = self.generate_query_from_keywords(model,
                                                       fulltextsearch,
                                                       **filters)

        if owner_id:
            subquery = self.db.session.query(Project)\
                           .with_entities(Project.id)\
                           .filter_by(owner_id=owner_id).subquery()
            query = self.db.session.query(model)\
                        .filter(model.project_id.in_(subquery), *query_args)
        else:
            query = self.db.session.query(model).filter(*query_args)
        return query

from project_repository import ProjectRepository
from user_repository import UserRepository
from blog_repository import BlogRepository
from task_repository import TaskRepository
from auditlog_repository import AuditlogRepository
from webhook_repository import WebhookRepository
from result_repository import ResultRepository

assert ProjectRepository
assert UserRepository
assert BlogRepository
assert TaskRepository
assert AuditlogRepository
assert WebhookRepository
assert ResultRepository
