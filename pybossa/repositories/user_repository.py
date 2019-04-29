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

from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from pybossa.repositories import Repository
from sqlalchemy import text
from pybossa.model.user import User
from pybossa.exc import WrongObjectError, DBIntegrityError
from sqlalchemy.orm.base import _entity_descriptor
from flask import current_app
import re
from pybossa.util import can_have_super_user_access, get_unique_user_preferences
from pybossa.model.task_run import TaskRun
from faker import Faker
from yacryptopan import CryptoPAn
import sqlalchemy

class UserRepository(Repository):

    def __init__(self, db):
        self.db = db

    def get(self, id):
        return self.db.session.query(User).get(id)

    def get_by_name(self, name):
        return self.db.session.query(User).filter_by(name=name).first()

    def get_by(self, **attributes):
        return self.db.session.query(User).filter_by(**attributes).first()

    def get_all(self):
        return self.db.session.query(User).filter_by(restrict=False).all()

    def filter_by(self, limit=None, offset=0, yielded=False, last_id=None,
                  fulltextsearch=None, desc=False, **filters):
        if filters.get('owner_id'):
            del filters['owner_id']
        # Force only restrict to False
        filters['restrict'] = False
        return self._filter_by(User, limit, offset, yielded,
                               last_id, fulltextsearch, desc, **filters)

    def filter_deleted_users(self, **filters):
        """Filter out deleted users."""
        filters['restrict'] = False
        query_args, queries, headlines, orders = self.generate_query_from_keywords(User, None, **filters)
        query = self.db.session.query(User).filter(*query_args)
        query = query.filter(sqlalchemy.not_(User.email_addr.contains(u'@del.com'))).order_by(User.id)
        return query.all()

    def search_by_name(self, keyword, **filters):
        if len(keyword) == 0:
            return []
        keyword = '%' + keyword.lower() + '%'
        query = self.db.session.query(User).filter(or_(func.lower(User.name).like(keyword),
                                  func.lower(User.fullname).like(keyword)))
        if filters:
            query = query.filter_by(**filters)
        return query.all()

    def search_by_name_orfilters(self, keyword, **filters):
        if len(keyword) == 0:
            return []
        keyword = '%' + keyword.lower() + '%'
        query = self.db.session.query(User).filter(or_(func.lower(User.name).like(keyword),
                                  func.lower(User.fullname).like(keyword)))
        if filters:
            or_clauses = []
            for k in filters.keys():
                or_clauses.append(_entity_descriptor(User, k) == filters[k])
            query = query.filter(or_(*or_clauses))
        return query.all()

    def total_users(self):
        return self.db.session.query(User).count()

    def lowercase_user_attributes(self, user):
        user.email_addr = user.email_addr.lower()

    def save(self, user):
        self._validate_can_be('saved', user)
        try:
            can_have_super_user_access(user)
            self.lowercase_user_attributes(user)
            self.db.session.add(user)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, new_user):
        self._validate_can_be('updated', new_user)
        try:
            can_have_super_user_access(new_user)
            self.lowercase_user_attributes(new_user)
            self.db.session.merge(new_user)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def fake_user_id(self, user):
        faker = Faker()
        cp = CryptoPAn(current_app.config.get('CRYPTOPAN_KEY'))
        task_runs = self.db.session.query(TaskRun).filter_by(user_id=user.id)
        for tr in task_runs:
            tr.user_id = None
            tr.user_ip = cp.anonymize(faker.ipv4())
            self.db.session.merge(tr)
            self.db.session.commit()

    def delete(self, user):
        self._validate_can_be('deleted', user)
        try:
            self.fake_user_id(user)
            self.db.session.delete(user)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete_data(self, user):
        self._validate_can_be('deleted', user)
        import uuid
        try:
            dummy = 'del-' + str(uuid.uuid4())
            user.name = dummy
            user.fullname = dummy
            user.email_addr = '{}@del.com'.format(dummy)
            user.enabled = False
            user.info = {}
            user.user_pref = {}
            self.db.session.merge(user)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def _validate_can_be(self, action, user):
        if not isinstance(user, User):
            name = user.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)

    def get_users(self, ids):
        if not ids:
            return []
        return self.db.session.query(User).filter(User.id.in_(ids)).all()

    def search_by_email(self, email_addr):
        return self.db.session.query(User).filter(func.lower(User.email_addr) == email_addr).first()

    def get_info_columns(self):
        return [u'languages', u'locations', u'work_hours_from', u'work_hours_to', u'timezone', u'user_type', u'additional_comments']

    def smart_search(self, current_user_is_admin, where, query_params):
        sql = text('''
                    SELECT id, name, fullname, info, enabled
                    FROM "user"
                    WHERE {where}
                    AND (:is_admin OR (NOT admin AND NOT subadmin));
                    '''.format(where=where))
        query_params['is_admin'] = current_user_is_admin
        results = self.db.session.execute(sql, query_params)
        return [dict(row) for row in results]

    def get_recent_contributor_emails(self, project_id):
        sql = text('''
                    SELECT DISTINCT email_addr
                    FROM "user" INNER JOIN task_run
                    ON (task_run.user_id = "user".id)
                    WHERE project_id = :project_id
                    AND current_timestamp - to_timestamp(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                        < interval '1 month';
                    ''')
        results = self.db.session.execute(sql, dict(project_id=project_id))
        return [row.email_addr for row in results]

    def get_user_pref_recent_contributor_emails(self, project_id, task_create_timestamp):
        # ongoing tasks user preferences
        sql = text('''
                    SELECT DISTINCT user_pref FROM task
                    WHERE project_id = :project_id
                    AND state = 'ongoing'
                    AND created >= :task_create_timestamp
                    AND user_pref::TEXT NOT IN ('null', '{}')
                    ''')
        results = self.db.session.execute(sql,
                    dict(project_id=project_id, task_create_timestamp=task_create_timestamp))
        task_prefs = [row.user_pref for row in results]
        dtask_prefs = get_unique_user_preferences(task_prefs) # distinct user prefs

        # user prefs for any ongoing tasks before task_create_timestamp that are to be excluded
        sql = text('''
                    SELECT DISTINCT user_pref FROM task
                    WHERE project_id = :project_id
                    AND state = 'ongoing'
                    AND created < :task_create_timestamp
                    AND user_pref::TEXT NOT IN ('null', '{}')
                    ''')
        results = self.db.session.execute(sql,
                    dict(project_id=project_id, task_create_timestamp=task_create_timestamp))
        exclude_task_prefs = [row.user_pref for row in results]
        dexclude_task_prefs = get_unique_user_preferences(exclude_task_prefs)   # distinct user prefs to exclude
        distinct_task_prefs = dtask_prefs - dexclude_task_prefs
        if not distinct_task_prefs:
            return []

        clauses = ('lower(user_pref::text)::jsonb @> lower({})::jsonb'.format(up) for up in distinct_task_prefs)
        user_prefs = ' AND ({})'.format(' OR '.join(clauses))

        sql = text('''
                    SELECT DISTINCT email_addr
                    FROM "user" INNER JOIN task_run
                    ON (task_run.user_id = "user".id)
                    WHERE project_id = :project_id {};
                    '''.format(user_prefs))
        current_app.logger.info(
            'get_user_pref_recent_contributor_emails Project {}: \
            task_pref {}, exclude_task_prefs {}, distinct_task_prefs {} \
            \n sql {}'.format(project_id, dtask_prefs, dexclude_task_prefs,
            distinct_task_prefs, str(sql)))

        results = self.db.session.execute(sql, dict(project_id=project_id))
        contributors = [ row.email_addr for row in results]
        current_app.logger.info('contributors {}'.format(contributors))
        return contributors

    def get_all_user_quizzes_for_project(self, project_id):
        sql = text('''
            SELECT id, fullname, info->'quiz'->'{0}' as quiz
            FROM "user"
            WHERE info->'quiz'->'{0}' IS NOT NULL
        '''.format(project_id))

        results = self.db.session.execute(sql)
        return results