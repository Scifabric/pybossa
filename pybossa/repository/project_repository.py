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

from pybossa.model.app import App
from pybossa.model.featured import Featured
from pybossa.model.category import Category



class ProjectRepository(object):


    def __init__(self, db):
        self.db = db


    def get(self, id):
        return self.db.session.query(App).get(id)

    def get_by_shortname(self, short_name):
        return self.db.session.query(App).filter_by(short_name=short_name).first()

    def get_by(self, **attributes):
        return self.db.session.query(App).filter_by(**attributes).first()

    def get_all(self):
        return self.db.session.query(App).all()

    def filter_by(self, **filters):
        return self.db.session.query(App).filter_by(**filters).all()

    def save(self, project):
        try:
            self.db.session.add(project)
            self.db.session.commit()
        except IntegrityError:
            self.db.session.rollback()
            raise

    def update(self, project):
        try:
            self.db.session.merge(project)
            self.db.session.commit()
        except IntegrityError:
            self.db.session.rollback()
            raise

    def delete(self, project):
        app = self.db.session.query(App).filter(App.id==project.id).first()
        self.db.session.delete(app)
        self.db.session.commit()



    def get_category(self, id=None):
        if id is None:
            return self.db.session.query(Category).first()
        return self.db.session.query(Category).get(id)

    def get_category_by(self, **attributes):
        return self.db.session.query(Category).filter_by(**attributes).first()

    def get_all_categories(self):
        return self.db.session.query(Category).all()

    def filter_categories_by(self, **filters):
        return self.db.session.query(Category).filter_by(**filters).all()

    def save_category(self, category):
        try:
            self.db.session.add(category)
            self.db.session.commit()
        except IntegrityError:
            self.db.session.rollback()
            raise

    def update_category(self, new_category):
        try:
            self.db.session.merge(new_category)
            self.db.session.commit()
        except IntegrityError:
            self.db.session.rollback()
            raise

    def delete_category(self, category):
        self.db.session.query(Category).filter(Category.id==category.id).delete()
        self.db.session.commit()

