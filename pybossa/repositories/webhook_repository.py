# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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

from pybossa.model.webhook import Webhook
from pybossa.exc import WrongObjectError, DBIntegrityError


class WebhookRepository(object):

    def __init__(self, db):
        self.db = db

    def get(self, id):
        return self.db.session.query(Webhook).get(id)

    def get_by(self, **attributes):
        return self.db.session.query(Webhook).filter_by(**attributes).first()

    def filter_by(self, limit=None, offset=0, **filters):
        query = self.db.session.query(Webhook).filter_by(**filters)
        query = query.order_by(Webhook.id).limit(limit).offset(offset)
        return query.all()

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

    def _validate_can_be(self, action, webhook):
        if not isinstance(webhook, Webhook):
            name = webhook.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
