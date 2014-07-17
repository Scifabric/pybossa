# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

from sqlalchemy.sql import text
from pybossa.cache import cache, delete_cached
from pybossa.core import db, timeouts, get_session
import pybossa.model as model


@cache(key_prefix="categories_all",
       timeout=timeouts.get('CATEGORY_TIMEOUT'))
def get_all():
    """Return all categories"""
    try:
        session = get_session(db, bind='slave')
        data = session.query(model.category.Category).all()
        return data
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


@cache(key_prefix="categories_used",
       timeout=timeouts.get('CATEGORY_TIMEOUT'))
def get_used():
    """Return categories only used by apps"""
    try:
        sql = text('''
                   SELECT category.* FROM category, app
                   WHERE app.category_id=category.id GROUP BY category.id
                   ''')
        session = get_session(db, bind='slave')
        results = session.execute(sql)
        categories = []
        for row in results:
            category = dict(id=row.id, name=row.name, short_name=row.short_name,
                            description=row.description)
            categories.append(category)
        return categories
    except: # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


def reset():
    """Clean the cache"""
    delete_cached('categories_all')
    delete_cached('categories_used')
