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
from pybossa.util import AttrDict
from pybossa.exc import WrongObjectError, DBIntegrityError


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
        return self.db.session.query(User).all()

    def filter_by(self, limit=None, offset=0, yielded=False, last_id=None,
                  fulltextsearch=None, desc=False, **filters):
        if filters.get('owner_id'):
            del filters['owner_id']
        return self._filter_by(User, limit, offset, yielded,
                               last_id, fulltextsearch, desc, **filters)

    def search_by_name(self, keyword, **filters):
        if len(keyword) == 0:
            return []
        keyword = '%' + keyword.lower() + '%'
        query = self.db.session.query(User).filter(or_(func.lower(User.name).like(keyword),
                                  func.lower(User.fullname).like(keyword)))
        if filters:
            query = query.filter_by(**filters)
        return query.all()

    def total_users(self):
        return self.db.session.query(User).count()

    def save(self, user):
        self._validate_can_be('saved', user)
        try:
            self.db.session.add(user)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, new_user):
        self._validate_can_be('updated', new_user)
        try:
            self.db.session.merge(new_user)
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
        return [u'languages', u'locations', u'start_time', u'end_time', u'timezone', u'user_type', u'additional_comments']

    def smart_search(self, current_user_is_admin, where, query_params):
        sql = text('''
                    SELECT id, name, fullname, info, enabled
                    FROM public.user
                    WHERE {where}
                    AND (:is_admin OR (NOT admin AND NOT subadmin));
                    '''.format(where=where))
        query_params['is_admin'] = current_user_is_admin
        results = self.db.session.execute(sql, query_params)
        return [dict(row) for row in results]

    def get_recent_contributor_emails(self, project_id):
        sql = text('''
                    SELECT DISTINCT email_addr
                    FROM public.user INNER JOIN task_run
                    ON (task_run.user_id = public.user.id)
                    WHERE project_id = :project_id
                    AND current_timestamp - to_timestamp(finish_time, 'YYYY-MM-DD"T"HH24:MI:SS.US')
                        < interval '1 month';
                    ''')
        results = self.db.session.execute(sql, dict(project_id=project_id))
        return [row.email_addr for row in results]
