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
from helper import web
from base import model, db


class Helper(web.Helper):
    """Class to help testing the scheduler"""
    def is_task(self, task_id, tasks):
        """Returns True if the task_id is in tasks list"""
        for t in tasks:
            if t.id == task_id:
                return True
        return False

    def is_unique(self, id, items):
        """Returns True if the id is not Unique"""
        copies = 0
        for i in items:
            if type(i) is dict:
                if i['id'] == id:
                    copies = copies + 1
            else:
                if i.id == id:
                    copies = copies + 1
        if copies >= 2:
            return False
        else:
            return True

    def del_task_runs(self, app_id=1):
        """Deletes all TaskRuns for a given app_id"""
        db.session.query(model.TaskRun).filter_by(app_id=1).delete()
        db.session.commit()
        db.session.remove()
