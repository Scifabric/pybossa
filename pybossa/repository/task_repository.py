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

from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun



class TaskRepository(object):


    def __init__(self, db):
        self.db = db


    def get_task(self, id):
        return self.db.session.query(Task).get(id)

    def get_task_by(self, **attributes):
        return self.db.session.query(Task).filter_by(**attributes).first()

    def filter_tasks_by(self, **filters):
        return self.db.session.query(Task).filter_by(**filters).all()

    def yield_filter_tasks_by(self, **filters):
        return self.db.session.query(Task).filter_by(**filters).yield_per(1)

    def count_tasks_with(self, **filters):
        return self.db.session.query(Task).filter_by(**filters).count()



    def get_task_run(self, id):
        return self.db.session.query(TaskRun).get(id)

    def get_task_run_by(self, **attributes):
        return self.db.session.query(TaskRun).filter_by(**attributes).first()

    def filter_task_runs_by(self, **filters):
        return self.db.session.query(TaskRun).filter_by(**filters).all()

    def yield_filter_task_runs_by(self, **filters):
        return self.db.session.query(TaskRun).filter_by(**filters).yield_per(1)

    def count_task_runs_with(self, **filters):
        return self.db.session.query(TaskRun).filter_by(**filters).count()



    def save(self, element):
        try:
            self.db.session.add(element)
            self.db.session.commit()
        except IntegrityError:
            self.db.session.rollback()
            raise

    def delete(self, element):
        self.db.session.delete(element)
        self.db.session.commit()

    def delete_all(self, elements):
        for element in elements:
            self.db.session.delete(element)
        self.db.session.commit()



