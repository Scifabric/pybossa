# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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

from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError

from pybossa.model.user import User
from pybossa.exc import WrongObjectError, DBIntegrityError



class UserRepository(object):


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

    def filter_by(self, **filters):
        return self.db.session.query(User).filter_by(**filters).all()

    def search_by_name(self, keyword):
        if len(keyword) == 0:
            return []
        keyword = '%' + keyword.lower() + '%'
        return self.db.session.query(User).filter(or_(func.lower(User.name).like(keyword),
                                  func.lower(User.fullname).like(keyword))).all()

    def total_users(self):
        return self.db.session.query(User).count()

    def save(self, user):
        if not isinstance(user, User):
            raise WrongObjectError('%s is not a User instance' % user)
        try:
            self.db.session.add(user)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, new_user):
        if not isinstance(new_user, User):
            raise WrongObjectError('%s is not a User instance' % new_user)
        try:
            self.db.session.merge(new_user)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)
