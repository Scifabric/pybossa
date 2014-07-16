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

from sqlalchemy.exc import IntegrityError

from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.exc import WrongObjectError, DBIntegrityError



class TaskRepository(object):


    def __init__(self, db):
        self.db = db


    # Methods for queries about Task objects
    def get_task(self, id):
        return self.db.session.query(Task).get(id)

    def get_task_by(self, **attributes):
        return self.db.session.query(Task).filter_by(**attributes).first()

    def filter_tasks_by(self, yielded=False, **filters):
        query = self.db.session.query(Task).filter_by(**filters)
        if yielded:
            return query.yield_per(1)
        return query.all()

    def count_tasks_with(self, **filters):
        return self.db.session.query(Task).filter_by(**filters).count()



    # Methods for queries about TaskRun objects
    def get_task_run(self, id):
        return self.db.session.query(TaskRun).get(id)

    def get_task_run_by(self, **attributes):
        return self.db.session.query(TaskRun).filter_by(**attributes).first()

    def filter_task_runs_by(self, yielded=False, **filters):
        query = self.db.session.query(TaskRun).filter_by(**filters)
        if yielded:
            return query.yield_per(1)
        return query.all()

    def count_task_runs_with(self, **filters):
        return self.db.session.query(TaskRun).filter_by(**filters).count()



    # Methods for save, delete and update both Task and TaskRun objects
    def save(self, element):
        if not isinstance(element, Task) and not isinstance(element, TaskRun):
            raise WrongObjectError('%s cannot be saved by TaskRepository' % element)
        try:
            self.db.session.add(element)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, element):
        if not isinstance(element, Task) and not isinstance(element, TaskRun):
            raise WrongObjectError('%s cannot be updated by TaskRepository' % element)
        try:
            self.db.session.merge(element)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete(self, element):
        if not isinstance(element, Task) and not isinstance(element, TaskRun):
            raise WrongObjectError('%s cannot be deleted by TaskRepository' % element)
        self.db.session.delete(element)
        self.db.session.commit()

    def delete_all(self, elements):
        for element in elements:
            if not isinstance(element, Task) and not isinstance(element, TaskRun):
                raise WrongObjectError('%s cannot be deleted by TaskRepository' % element)
            self.db.session.delete(element)
        self.db.session.commit()
