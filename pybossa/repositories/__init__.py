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
    * project_stats_repo
    * announcement_repo
    * blog_repo
    * task_repo
    * auditlog_repo
    * webhook_repo
    * result_repo
    * helpingmaterial_repo
    * page_repo

The responsibility of these repositories is only fetching one
or many objects of kind and/or saving them to the DB by calling
the ORM apropriate methods.

For more complex DB queries, refer to other packages or services within
PYBOSSA.
"""
import json
import re
from pybossa.model.project import Project, TaskRun, Task
from pybossa.model.announcement import Announcement
from pybossa.model.project_stats import ProjectStats
from sqlalchemy import text
from sqlalchemy.sql import and_, or_
from sqlalchemy import cast, func, desc
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm.base import _entity_descriptor


class Repository(object):

    def __init__(self, db, language='english'):
        self.db = db
        self.language = language

    def generate_query_from_keywords(self, model, fulltextsearch=None,
                                     **kwargs):
        clauses = [_entity_descriptor(model, key) == value
                       for key, value in list(kwargs.items())
                       if (key != 'info' and key != 'fav_user_ids'
                            and key != 'created' and key != 'project_id')]
        queries = []
        headlines = []
        order_by_ranks = []
        or_clauses = []

        if 'info' in list(kwargs.keys()):
            queries, headlines, order_by_ranks = self.handle_info_json(model, kwargs['info'],
                                                                       fulltextsearch)
            clauses = clauses + queries

        if 'created' in list(kwargs.keys()):
            like_query = kwargs['created'] + '%'
            clauses.append(
                _entity_descriptor(model, 'created').like(like_query))

        if 'project_id' in list(kwargs.keys()):
            tmp = "%s" % kwargs['project_id']
            project_ids = re.findall(r'\d+', tmp)
            for project_id in project_ids:
                or_clauses.append((_entity_descriptor(model, 'project_id') ==
                                   project_id))
        all_clauses = and_(and_(*clauses), or_(*or_clauses))
        return (all_clauses,), queries, headlines, order_by_ranks

    def handle_info_json(self, model, info, fulltextsearch=None):
        """Handle info JSON query filter."""
        clauses = []
        headlines = []
        order_by_ranks = []

        if info and '::' in info:
            pairs = info.split('|')
            for pair in pairs:
                if pair != '':
                    k, v = pair.split("::")
                    if fulltextsearch == '1':
                        vector = _entity_descriptor(model, 'info')[k].astext
                        clause = func.to_tsvector(vector).match(v)
                        clauses.append(clause)
                        if len(headlines) == 0:
                            headline = func.ts_headline(
                                self.language,
                                vector,
                                func.to_tsquery(v))
                            headlines.append(headline)
                            order = func.ts_rank_cd(
                                func.to_tsvector(vector),
                                func.to_tsquery(v), 4).label('rank')
                            order_by_ranks.append(order)
                    else:
                        clauses.append(
                            _entity_descriptor(model, 'info')[k].astext == v)
        else:
            if type(info) == dict:
                clauses.append(_entity_descriptor(model, 'info') == info)
            if type(info) == str or type(info) == str:
                try:
                    info = json.loads(info)
                    if type(info) == int or type(info) == float:
                        info = '"%s"' % info
                except ValueError:
                    info = '"%s"' % info
                clauses.append(_entity_descriptor(model,
                                                  'info').contains(info))
        return clauses, headlines, order_by_ranks

    def create_context(self, filters, fulltextsearch, model):
        """Return query with context aware query."""
        owner_id = None
        query = None
        participated = None

        if filters.get('owner_id'):
            owner_id = filters.get('owner_id')
            del filters['owner_id']

        # Prevent external_uid for taks & participated arg
        if filters.get('participated') and filters.get('external_uid'):
            del filters['external_uid']

        if filters.get('participated'):
            participated = filters.get('participated')
            del filters['participated']

        query_args, queries, headlines, orders = self.generate_query_from_keywords(
            model, fulltextsearch,
            **filters)

        if model not in [Announcement, ProjectStats] and owner_id:
            subquery = self.db.session.query(Project)\
                           .with_entities(Project.id)\
                           .filter_by(owner_id=owner_id).subquery()
            if (model != Project):
                query = self.db.session.query(model)\
                            .filter(model.project_id.in_(subquery),
                                    *query_args)
            else:
                query = self.db.session.query(model)\
                            .filter(model.id.in_(subquery),
                                    *query_args)
        else:
            query = self.db.session.query(model).filter(*query_args)

        if participated and model == Task:
            if participated['user_id']:
                subquery = self.db.session.query(TaskRun)\
                               .with_entities(TaskRun.task_id)\
                               .filter_by(
                                   user_id=participated['user_id']).subquery()
            if participated['external_uid']:
                subquery = self.db.session.query(TaskRun)\
                               .with_entities(TaskRun.task_id)\
                               .filter_by(external_uid=participated['external_uid']).subquery()
            if participated['user_ip']:
                subquery = self.db.session.query(TaskRun)\
                               .with_entities(TaskRun.task_id)\
                               .filter_by(user_ip=participated['user_ip']).subquery()
            query = self.db.session.query(model)\
                        .filter(~model.id.in_(subquery),
                                *query_args)
        if len(headlines) > 0:
            query = query.add_column(headlines[0])
        if len(orders) > 0:
            query = query.add_column(orders[0])
            query = query.order_by(text('rank DESC'))
        return query

    def _set_orderby_desc(self, query, model, limit,
                          last_id, offset, descending, orderby):
        """Return an updated query with the proper orderby and desc."""
        if orderby == 'fav_user_ids':
            n_favs = func.coalesce(func.array_length(model.fav_user_ids, 1), 0).label('n_favs')
            query = query.add_column(n_favs)
        if orderby in ['created', 'updated', 'finish_time']:
            if descending:
                query = query.order_by(desc(
                                            cast(getattr(model,
                                                         orderby),
                                                 TIMESTAMP)))
            else:
                query = query.order_by(cast(getattr(model, orderby), TIMESTAMP))
        else:
            if orderby != 'fav_user_ids':
                if descending:
                    query = query.order_by(desc(getattr(model, orderby)))
                else:
                    query = query.order_by(getattr(model, orderby))
            else:
                if descending:
                    query = query.order_by(desc(text("n_favs")))
                else:
                    query = query.order_by(text("n_favs"))
        if last_id:
            query = query.limit(limit)
        else:
            query = query.limit(limit).offset(offset)
        return query

    def _filter_by(self, model, limit=None, offset=0, yielded=False,
                   last_id=None, fulltextsearch=None, desc=False,
                   orderby='id', **filters):
        """Filter by using several arguments and ordering items."""
        query = self.create_context(filters, fulltextsearch, model)
        if last_id:
            query = query.filter(model.id > last_id)
            query = self._set_orderby_desc(query, model, limit,
                                           last_id, offset, desc, orderby)
        else:
            query = self._set_orderby_desc(query, model, limit,
                                           last_id, offset, desc, orderby)
        if yielded:
            limit = limit or 1
            return query.yield_per(limit)
        return query.all()


from .project_repository import ProjectRepository
from .project_stats_repository import ProjectStatsRepository
from .user_repository import UserRepository
from .announcement_repository import AnnouncementRepository
from .blog_repository import BlogRepository
from .task_repository import TaskRepository
from .auditlog_repository import AuditlogRepository
from .webhook_repository import WebhookRepository
from .result_repository import ResultRepository
from .helping_repository import HelpingMaterialRepository
from .page_repository import PageRepository

assert ProjectRepository
assert ProjectStatsRepository
assert UserRepository
assert AnnouncementRepository
assert BlogRepository
assert TaskRepository
assert AuditlogRepository
assert WebhookRepository
assert ResultRepository
assert HelpingMaterialRepository
assert PageRepository
