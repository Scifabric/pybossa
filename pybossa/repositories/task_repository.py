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

import json
from sqlalchemy.sql import text, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.base import _entity_descriptor
from sqlalchemy import cast
from sqlalchemy import Text

from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.exc import WrongObjectError, DBIntegrityError
from pybossa.cache import projects as cached_projects
from pybossa.core import uploader


def generate_query_from_keywords(model, **kwargs):
    clauses = [_entity_descriptor(model, key) == value
                   for key, value in kwargs.items()
                   if key != 'info']
    if 'info' in kwargs.keys():
        info = json.dumps(kwargs['info'])
        clauses.append(cast(_entity_descriptor(model, 'info'), Text) == info)
    return and_(*clauses) if len(clauses) != 1 else (and_(*clauses), )


class TaskRepository(object):

    def __init__(self, db):
        self.db = db

    # Methods for queries on Task objects
    def get_task(self, id):
        return self.db.session.query(Task).get(id)

    def get_task_by(self, **attributes):
        filters = generate_query_from_keywords(Task, **attributes)
        return self.db.session.query(Task).filter(*filters).first()

    def filter_tasks_by(self, limit=None, offset=0, yielded=False,
                        last_id=None, **filters):
        query_args = generate_query_from_keywords(Task, **filters)
        query = self.db.session.query(Task).filter(*query_args)
        if last_id:
            query = query.filter(Task.id > last_id)
            query = query.order_by(Task.id).limit(limit)
        else:
            query = query.order_by(Task.id).limit(limit).offset(offset)
        if yielded:
            limit = limit or 1
            return query.yield_per(limit)
        return query.all()

    def count_tasks_with(self, **filters):
        query_args = generate_query_from_keywords(Task, **filters)
        return self.db.session.query(Task).filter(*query_args).count()


    # Methods for queries on TaskRun objects
    def get_task_run(self, id):
        return self.db.session.query(TaskRun).get(id)

    def get_task_run_by(self, **attributes):
        filters = generate_query_from_keywords(TaskRun, **attributes)
        return self.db.session.query(TaskRun).filter(*filters).first()

    def filter_task_runs_by(self, limit=None, offset=0, last_id=None,
                            yielded=False, **filters):
        query_args = generate_query_from_keywords(TaskRun, **filters)
        query = self.db.session.query(TaskRun).filter(*query_args)
        if last_id:
            query = query.filter(TaskRun.id > last_id)
            query = query.order_by(TaskRun.id).limit(limit)
        else:
            query = query.order_by(TaskRun.id).limit(limit).offset(offset)
        if yielded:
            limit = limit or 1
            return query.yield_per(limit)
        return query.all()

    def count_task_runs_with(self, **filters):
        query_args = generate_query_from_keywords(TaskRun, **filters)
        return self.db.session.query(TaskRun).filter(*query_args).count()


    # Methods for saving, deleting and updating both Task and TaskRun objects
    def save(self, element):
        self._validate_can_be('saved', element)
        try:
            self.db.session.add(element)
            self.db.session.commit()
            cached_projects.clean_project(element.project_id)
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, element):
        self._validate_can_be('updated', element)
        try:
            self.db.session.merge(element)
            self.db.session.commit()
            cached_projects.clean_project(element.project_id)
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete(self, element):
        self._delete(element)
        project = element.project
        self.db.session.commit()
        cached_projects.clean_project(element.project_id)
        self._delete_zip_files_from_store(project)

    def delete_valid_from_project(self, project):
        """Delete only tasks that have no results associated."""
        sql = text('''
                   DELETE FROM task WHERE task.project_id=:project_id
                   AND task.id NOT IN
                   (SELECT task_id FROM result
                   WHERE result.project_id=:project_id GROUP BY result.task_id);
                   ''')
        self.db.session.execute(sql, dict(project_id=project.id))
        self.db.session.commit()
        cached_projects.clean_project(project.id)
        self._delete_zip_files_from_store(project)

    def delete_taskruns_from_project(self, project):
        sql = text('''
                   DELETE FROM task_run WHERE project_id=:project_id;
                   ''')
        self.db.session.execute(sql, dict(project_id=project.id))
        self.db.session.commit()
        cached_projects.clean_project(project.id)
        self._delete_zip_files_from_store(project)

    def update_tasks_redundancy(self, project, n_answer):
        """update the n_answer of every task from a project and their state.
        Use raw SQL for performance"""
        sql = text('''
                   UPDATE task SET n_answers=:n_answers,
                   state='ongoing' WHERE project_id=:project_id''')
        self.db.session.execute(sql, dict(n_answers=n_answer, project_id=project.id))
        # Update task.state according to their new n_answers value
        sql = text('''
                   WITH project_tasks AS (
                   SELECT task.id, task.n_answers,
                   COUNT(task_run.id) AS n_task_runs, task.state
                   FROM task, task_run
                   WHERE task_run.task_id=task.id AND task.project_id=:project_id
                   GROUP BY task.id)
                   UPDATE task SET state='completed'
                   FROM project_tasks
                   WHERE (project_tasks.n_task_runs >=:n_answers)
                   and project_tasks.id=task.id
                   ''')
        self.db.session.execute(sql, dict(n_answers=n_answer, project_id=project.id))
        self.db.session.commit()
        cached_projects.clean_project(project.id)

    def _validate_can_be(self, action, element):
        if not isinstance(element, Task) and not isinstance(element, TaskRun):
            name = element.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)

    def _delete(self, element):
        self._validate_can_be('deleted', element)
        table = element.__class__
        inst = self.db.session.query(table).filter(table.id==element.id).first()
        self.db.session.delete(inst)

    def _delete_zip_files_from_store(self, project):
        from pybossa.core import json_exporter, csv_exporter
        global uploader
        if uploader is None:
            from pybossa.core import uploader
        json_tasks_filename = json_exporter.download_name(project, 'task')
        csv_tasks_filename = csv_exporter.download_name(project, 'task')
        json_taskruns_filename = json_exporter.download_name(project, 'task_run')
        csv_taskruns_filename = csv_exporter.download_name(project, 'task_run')
        container = "user_%s" % project.owner_id
        uploader.delete_file(json_tasks_filename, container)
        uploader.delete_file(csv_tasks_filename, container)
        uploader.delete_file(json_taskruns_filename, container)
        uploader.delete_file(csv_taskruns_filename, container)
