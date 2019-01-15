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
from pybossa.model.user import User
from pybossa.model.task_run import TaskRun
from pybossa.exc import WrongObjectError, DBIntegrityError
from faker import Faker
from yacryptopan import CryptoPAn
from flask import current_app


class UserRepository(Repository):

    def __init__(self, db):
        self.db = db

    def get(self, id):
        return self.db.session.query(User).get(id)

    def get_by_name(self, name):
        tmp = name
        if type(name) == bytes:
            tmp = name.decode('utf-8')
        return self.db.session.query(User).filter_by(name=tmp).first()

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

    def search_by_name(self, keyword):
        if len(keyword) == 0:
            return []
        keyword = '%' + keyword.lower() + '%'
        return self.db.session.query(User).filter(or_(func.lower(User.name).like(keyword),
                                  func.lower(User.fullname).like(keyword))).all()

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

    def fake_user_id(self, user):
        faker = Faker()
        cp = CryptoPAn(current_app.config.get('CRYPTOPAN_KEY').encode('utf-8'))
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

    def _validate_can_be(self, action, user):
        if not isinstance(user, User):
            name = user.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)

    def get_users(self, ids):
        if not ids:
            return []
        return self.db.session.query(User).filter(User.id.in_(ids)).all()
