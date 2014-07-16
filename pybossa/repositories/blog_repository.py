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

from sqlalchemy.exc import IntegrityError

from pybossa.model.blogpost import Blogpost
from pybossa.exc import WrongObjectError, DBIntegrityError



class BlogRepository(object):


    def __init__(self, db):
        self.db = db


    def get(self, id):
        return self.db.session.query(Blogpost).get(id)

    def get_by(self, **attributes):
        return self.db.session.query(Blogpost).filter_by(**attributes).first()

    def filter_by(self, **filters):
        return self.db.session.query(Blogpost).filter_by(**filters).all()

    def save(self, blogpost):
        self._validate_can_be('saved', blogpost)
        try:
            self.db.session.add(blogpost)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, blogpost):
        self._validate_can_be('updated', blogpost)
        try:
            self.db.session.merge(blogpost)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete(self, blogpost):
        self._validate_can_be('deleted', blogpost)
        blog = self.db.session.query(Blogpost).filter(Blogpost.id==blogpost.id).first()
        self.db.session.delete(blog)
        self.db.session.commit()


    def _validate_can_be(self, action, blogpost):
        if not isinstance(blogpost, Blogpost):
            name = blogpost.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
