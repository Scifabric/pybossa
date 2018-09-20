# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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

"""
CategorySyncer module for syncing projects on different domains.
"""

import json
from flask import current_app
from pybossa.syncer import Syncer, SyncUnauthorized


class CategorySyncer(Syncer):
    """Syncs one category with another."""

    _api_endpoint = 'category'
    reserved_keys = ('id', 'created', 'links', 'link')

    def sync(self, category):
        target = self.get_target(name=category.name)

        if not target:
            payload = self._build_payload(category)
            current_app.logger.info(
                    'Syncing category: {}'.format(payload))
            res =  self._create(payload, self.target_key)
            if res.reason == 'FORBIDDEN':
                raise SyncUnauthorized(self.__class__.__name__)
            return res

    def _build_payload(self, obj):
        payload = self._remove_reserved_keys(obj.dictize())
        payload = self._add_sync_info(payload)
        return payload
