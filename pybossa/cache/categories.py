# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.
from sqlalchemy.sql import text
from pybossa.core import cache
from pybossa.core import db
import pybossa.model as model


@cache.cached(key_prefix="categories_all")
def get_all():
    """Return all categories"""
    return db.session.query(model.Category).all()


@cache.cached(key_prefix="categories_used")
def get_used():
    """Return categories only used by apps"""
    sql = text('''
               SELECT category.* FROM category, app
               WHERE app.category_id=category.id GROUP BY category.id
               ''')
    results = db.engine.execute(sql)
    categories = []
    for row in results:
        category = dict(id=row.id, name=row.name, short_name=row.short_name,
                        description=row.description)
        categories.append(category)
    return categories


def reset():
    """Clean the cache"""
    cache.delete('categories_all')
    cache.delete('categories_used')
