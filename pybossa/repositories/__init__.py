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
PYBOSSA.
"""
import json
from pybossa.model.project import Project
from sqlalchemy.sql import and_
from sqlalchemy import cast, Text, func, Date
from sqlalchemy.orm.base import _entity_descriptor

class Repository(object):

    def __init__(self, db, language='english'):
        self.db = db
        self.language = language

    def generate_query_from_keywords(self, model, fulltextsearch=None,
                                     **kwargs):
        print model
        clauses = [_entity_descriptor(model, key) == value
                       for key, value in kwargs.items()
                       if key != 'info']
        queries = []
        headlines = []
        order_by_ranks = []
        if 'info' in kwargs.keys():
            #clauses = clauses + self.handle_info_json(model, kwargs['info'],
            #                                          fulltextsearch)
            queries, headlines, order_by_ranks = self.handle_info_json(model, kwargs['info'],
                                                                       fulltextsearch)
            clauses = clauses + queries
        if len(clauses) != 1:
            return and_(*clauses), queries, headlines, order_by_ranks
        else:
            return (and_(*clauses), ), queries, headlines, order_by_ranks


    def handle_info_json(self, model, info, fulltextsearch=None):
        """Handle info JSON query filter."""
        clauses = []
        headlines = []
        order_by_ranks = []
        if '::' in info:
            pairs = info.split('|')
            for pair in pairs:
                if pair != '':
                    k,v = pair.split("::")
                    if fulltextsearch == '1':
                        vector = _entity_descriptor(model, 'info')[k].astext
                        clause = func.to_tsvector(vector).match(v)
                        clauses.append(clause)
                        if len(headlines) == 0:
                            headline = func.ts_headline(self.language, vector, func.to_tsquery(v))
                            headlines.append(headline)
                            order = func.ts_rank_cd(func.to_tsvector(vector), func.to_tsquery(v), 4).label('rank')
                            order_by_ranks.append(order)
                    else:
                        clauses.append(_entity_descriptor(model,
                                                          'info')[k].astext == v)
        else:
            info = json.dumps(info)
            clauses.append(cast(_entity_descriptor(model, 'info'),
                                Text) == info)
        return clauses, headlines, order_by_ranks


    def create_context(self, filters, fulltextsearch, model):
        """Return query with context aware query."""
        owner_id = None
        query = None

        if filters.get('owner_id'):
            owner_id = filters.get('owner_id')
            del filters['owner_id']
        data = self.generate_query_from_keywords(model,
                         fulltextsearch,
                         **filters)

        query_args, queries, headlines, orders = self.generate_query_from_keywords(model,
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
        if len(headlines) > 0:
            query = query.add_column(headlines[0])
        if len(orders) > 0:
            query = query.add_column(orders[0])
            query = query.order_by('rank DESC')
        return query

    def _filter_by(self, model, limit=None, offset=0, yielded=False,
                  last_id=None, fulltextsearch=None, desc=False,
                  **filters):
        """Filter by using several arguments and ordering items."""
        query = self.create_context(filters, fulltextsearch, model)
        if last_id:
            query = query.filter(model.id > last_id)
            query = query.order_by(model.id).limit(limit)
        else:
            if desc:
                query = query.order_by(cast(model.created, Date).desc())\
                        .limit(limit).offset(offset)
            else:
                query = query.order_by(model.id).limit(limit).offset(offset)

        if yielded:
            limit = limit or 1
            return query.yield_per(limit)
        return query.all()


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
