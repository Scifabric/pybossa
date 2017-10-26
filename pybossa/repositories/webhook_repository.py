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

from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from pybossa.cache.projects import clean_project
from pybossa.repositories import Repository
from pybossa.model.webhook import Webhook
from pybossa.exc import WrongObjectError, DBIntegrityError


class WebhookRepository(Repository):

    def __init__(self, db):
        self.db = db

    def get(self, id):
        return self.db.session.query(Webhook).get(id)

    def get_by(self, **attributes):
        return self.db.session.query(Webhook).filter_by(**attributes).first()

    def filter_by(self, limit=None, offset=0, **filters):
        return self._filter_by(Webhook, limit, offset, **filters)

    def save(self, webhook):
        self._validate_can_be('saved', webhook)
        try:
            self.db.session.add(webhook)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, webhook):
        self._validate_can_be('updated', webhook)
        try:
            self.db.session.merge(webhook)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete_entries_from_project(self, project):
        sql = text('''
                   DELETE FROM webhook WHERE project_id=:project_id;
                   ''')
        self.db.session.execute(sql, dict(project_id=project.id))
        self.db.session.commit()
        clean_project(project.id)

    def _validate_can_be(self, action, webhook):
        if not isinstance(webhook, Webhook):
            name = webhook.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
