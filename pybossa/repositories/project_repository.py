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
from flask.ext.login import current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import get_history
from sqlalchemy import inspect

from pybossa.model.app import App
from pybossa.model.auditlog import Auditlog
from pybossa.model.category import Category
from pybossa.exc import WrongObjectError, DBIntegrityError


class ProjectRepository(object):


    def __init__(self, db):
        self.db = db


    # Methods for App/Project objects
    def get(self, id):
        return self.db.session.query(App).get(id)

    def get_by_shortname(self, short_name):
        return self.db.session.query(App).filter_by(short_name=short_name).first()

    def get_by(self, **attributes):
        return self.db.session.query(App).filter_by(**attributes).first()

    def get_all(self):
        return self.db.session.query(App).all()

    def filter_by(self, limit=None, offset=0, **filters):
        query = self.db.session.query(App).filter_by(**filters)
        query = query.order_by(App.id).limit(limit).offset(offset)
        return query.all()

    def save(self, project):
        self._validate_can_be('saved', project)
        try:
            self.db.session.add(project)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, project):
        action = 'updated'
        self._validate_can_be(action, project)
        try:
            self.add_log_entry(project, action)
            self.db.session.add(project)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete(self, project):
        self._validate_can_be('deleted', project)
        app = self.db.session.query(App).filter(App.id==project.id).first()
        self.db.session.delete(app)
        self.db.session.commit()

    def add_log_entry(self, project, action):
        try:
            for attr in project.dictize().keys():
                if getattr(inspect(project).attrs, attr).history.has_changes():
                    history = getattr(inspect(project).attrs, attr).history
                    if len(history.deleted) > 0 and len(history.added) > 0:
                        msg = ("User %s updated %s attribute from: %s to: %s" %
                               (current_user.name,
                                attr,
                                history.deleted[0],
                                history.added[0]))
                        log = Auditlog(
                            app_id=project.id,
                            app_short_name=project.short_name,
                            user_id=current_user.id,
                            user_name=current_user.name,
                            action=action,
                            log=msg)
                        self.db.session.add(log)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    # Methods for Category objects
    def get_category(self, id=None):
        if id is None:
            return self.db.session.query(Category).first()
        return self.db.session.query(Category).get(id)

    def get_category_by(self, **attributes):
        return self.db.session.query(Category).filter_by(**attributes).first()

    def get_all_categories(self):
        return self.db.session.query(Category).all()

    def filter_categories_by(self, limit=None, offset=0, **filters):
        query = self.db.session.query(Category).filter_by(**filters)
        query = query.order_by(Category.id).limit(limit).offset(offset)
        return query.all()

    def save_category(self, category):
        self._validate_can_be('saved as a Category', category, klass=Category)
        try:
            self.db.session.add(category)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update_category(self, new_category):
        self._validate_can_be('updated as a Category', new_category, klass=Category)
        try:
            self.db.session.merge(new_category)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete_category(self, category):
        self._validate_can_be('deleted as a Category', category, klass=Category)
        self.db.session.query(Category).filter(Category.id==category.id).delete()
        self.db.session.commit()


    def _validate_can_be(self, action, element, klass=App):
        if not isinstance(element, klass):
            name = element.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
