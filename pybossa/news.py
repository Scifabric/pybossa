
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
from pybossa.core import sentinel
from pybossa.core import db
try:
    import pickle as pickle
except ImportError:  # pragma: no cover
    import pickle


FEED_KEY = 'scifabricnews'
NOTIFY_ADMIN = 'notify:admin:'

def get_news(score=None):
    """Return news list."""
    minscore = 0
    maxscore = 5
    if score:
        minscore = score
        maxscore = score
    data = sentinel.slave.zrangebyscore(FEED_KEY, minscore, maxscore,
                                        withscores=True)
    news = []
    for u in data:
        tmp = pickle.loads(u[0])
        news.append(tmp)
    return news


def notify_news_admins():
    """Notify news admins."""
    from pybossa.repositories import UserRepository

    user_repo = UserRepository(db)
    admins = user_repo.filter_by(admin=True)

    for admin in admins:
        key = NOTIFY_ADMIN + str(admin.id)
        sentinel.master.set(key, 1)
