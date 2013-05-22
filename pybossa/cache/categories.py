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
from pybossa.core import cache
from pybossa.core import db
import pybossa.model as model


STATS_TIMEOUT = 50


@cache.cached(key_prefix="categories")
def get():
    """Return categories"""
    return db.session.query(model.Category).all()


def reset():
    """Clean the cache"""
    cache.delete('categories')
