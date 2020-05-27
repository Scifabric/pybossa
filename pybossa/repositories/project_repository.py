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

from sqlalchemy.exc import IntegrityError
from sqlalchemy import cast, Date
from sqlalchemy.sql import text

from pybossa.repositories import Repository
from pybossa.model.project import Project
from pybossa.model.category import Category
from pybossa.exc import WrongObjectError, DBIntegrityError
from pybossa.cache import projects as cached_projects
from pybossa.core import uploader
from werkzeug.exceptions import BadRequest
import pandas.io.sql as sqlio
import pandas as pd
from flask import current_app


class ProjectRepository(Repository):

    # Methods for Project objects
    def get(self, id):
        return self.db.session.query(Project).get(id)

    def get_by_shortname(self, short_name):
        return self.db.session.query(Project).filter_by(short_name=short_name).first()

    def get_by(self, **attributes):
        return self.db.session.query(Project).filter_by(**attributes).first()

    def get_all(self):
        return self.db.session.query(Project).all()

    def filter_by(self, limit=None, offset=0, yielded=False, last_id=None,
                  fulltextsearch=None, desc=False, **filters):
        if filters.get('owner_id'):
            filters['owner_id'] = filters.get('owner_id')
        return self._filter_by(Project, limit, offset, yielded, last_id,
                               fulltextsearch, desc, **filters)

    def save(self, project):
        self._validate_can_be('saved', project)
        self._empty_strings_to_none(project)
        self._creator_is_owner(project)
        self._verify_has_password(project)
        self._verify_data_classification(project)

        try:
            self.db.session.add(project)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, project):
        self._validate_can_be('updated', project)
        self._empty_strings_to_none(project)
        self._creator_is_owner(project)
        self._verify_has_password(project)
        self._verify_data_classification(project)
        try:
            self.db.session.merge(project)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete(self, project):
        self._validate_can_be('deleted', project)
        project = self.db.session.query(Project).filter(Project.id==project.id).first()
        self.db.session.delete(project)
        self.db.session.commit()
        cached_projects.clean(project.id)
        self._delete_zip_files_from_store(project)


    # Methods for Category objects
    def get_category(self, id=None):
        if id is None:
            return self.db.session.query(Category).first()
        return self.db.session.query(Category).get(id)

    def get_category_by(self, **attributes):
        return self.db.session.query(Category).filter_by(**attributes).first()

    def get_all_categories(self):
        return self.db.session.query(Category).all()

    def filter_categories_by(self, limit=None, offset=0, yielded=False,
                             last_id=None, fulltextsearch=None,
                             orderby='id',
                             desc=False, **filters):
        if filters.get('owner_id'):
            del filters['owner_id']
        return self._filter_by(Category, limit, offset, yielded, last_id,
                               fulltextsearch, desc, orderby, **filters)

    def save_category(self, category):
        self._validate_can_be('saved as a Category', category, klass=Category)
        try:
            self.db.session.add(category)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update_category(self, new_category, caller="web"):
        self._validate_can_be('updated as a Category', new_category, klass=Category)
        try:
            self.db.session.merge(new_category)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def delete_category(self, category):
        self._validate_can_be('deleted as a Category', category, klass=Category)
        self.db.session.query(Category).filter(Category.id==category.id).delete()
        self.db.session.commit()

    def _empty_strings_to_none(self, project):
        if project.name == '':
            project.name = None
        if project.short_name == '':
            project.short_name = None
        if project.description == '':
            project.description = None

    def _creator_is_owner(self, project):
        if project.owners_ids is None:
            project.owners_ids = []
        if project.owner_id not in project.owners_ids:
            project.owners_ids.append(project.owner_id)

    def _verify_has_password(self, project):
        if not project.info.get('passwd_hash'):
            raise BadRequest('Project must have a password')

    def _verify_data_classification(self, project):
        # validate data classification
        if not project.info.get('data_classification'):
            raise BadRequest('Project must have a data classification for input and output data')

        input_data_class = project.info.get('data_classification', {}).get('input_data')
        output_data_class = project.info.get('data_classification', {}).get('output_data')
        if not (input_data_class and output_data_class):
            raise BadRequest('Project must have input data classification and output data classification')

        data_classification = current_app.config.get('DATA_CLASSIFICATION', [])
        valid_data_classes = current_app.config.get('VALID_DATA_CLASSES', [])
        if input_data_class not in valid_data_classes:
            raise BadRequest('Project must have valid input data classification')
        if output_data_class not in valid_data_classes:
            raise BadRequest('Project must have valid output data classification')
        input_output_data_access = [input_data_class.split('-')[0].strip(), output_data_class.split('-')[0].strip()]

        # set data access level with highest level between input and output data access classifications
        valid_data_access = current_app.config.get('VALID_ACCESS_LEVELS', [])
        data_access = []
        for data_access_level in valid_data_access:
            if data_access_level in input_output_data_access:
                data_access = data_access_level
                break
        if data_access:
            project.info['data_access'] = [data_access]


    def _validate_can_be(self, action, element, klass=Project):
        if not isinstance(element, klass):
            name = element.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)

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

    def get_projects_report(self, base_url):
        sql_completed_tasks = text(
            '''
                SELECT
                   task.project_id,
                   COUNT(DISTINCT task.id) AS completed_tasks,
                   MAX(task_run.finish_time) AS finish_time
                FROM task INNER JOIN task_run on task.id = task_run.task_id
                WHERE task.state = 'completed'
                GROUP BY task.project_id
                ORDER BY project_id;
            '''
            )

        sql_total_tasks = text(
            '''
             SELECT
                project_id,
                COUNT(task.id) AS n_tasks
             FROM task
             GROUP BY project_id
            ORDER BY project_id;
            '''
            )

        sql_n_workers = text(
            '''
            SELECT
                project_id,
                count(distinct user_id) as n_workers
            FROM task_run INNER JOIN "user"
            ON task_run.user_id = "user".id
            GROUP BY project_id
            ORDER BY project_id;
            '''
            )

        sql_n_taskruns = text(
            '''
            SELECT project_id,
                COUNT(id) AS n_taskruns,
                MAX(finish_time) as last_submission
            FROM task_run
            GROUP BY project_id
            ORDER BY project_id;
            '''
            )

        sql_n_pending_taskruns = text(
            '''
            SELECT project_id,
                SUM(task.n_answers - COALESCE(t.actual_answers, 0)) AS n_pending_taskruns
            FROM task
            LEFT JOIN (
            SELECT task_id,
                   COUNT(id) AS actual_answers
            FROM task_run
            GROUP BY task_id) AS t
            ON task.id = t.task_id
            WHERE task.state = 'ongoing'
            GROUP BY project_id
            ORDER BY project_id;
            '''
            )

        sql_project_details = text(
            '''
            SELECT project.id AS project_id,
            project.name AS name,
            project.short_name AS short_name,
            project.long_description AS long_description,
            project.created AS created,
            category.name AS category_name,
            "user".name AS owner_name,
            "user".email_addr AS owner_email,
            project.updated AS updated
            FROM project JOIN category
            ON project.category_id = category.id
            JOIN "user" ON project.owner_id = "user".id
            ORDER BY project_id;
            '''
            )

        sql_worker_details = text(
            '''
            SELECT project.id AS project_id,
            STRING_AGG(CONCAT('(', workers.user_id, ';', workers.fullname, ';', workers.email_addr, ')'), '|')
            AS workers FROM project JOIN
            (
                SELECT DISTINCT
                project_id, user_id,
                "user".fullname, "user".email_addr
                FROM task_run INNER JOIN "user"
                ON task_run.user_id = "user".id ORDER BY project_id
            ) workers ON
            project.id = workers.project_id
            GROUP BY project.id
            ORDER BY project.id;
            '''
            )

        # query database to get different report data
        completed_tasks = sqlio.read_sql_query(sql_completed_tasks, self.db.engine)
        total_tasks = sqlio.read_sql_query(sql_total_tasks, self.db.engine)
        n_workers = sqlio.read_sql_query(sql_n_workers, self.db.engine)
        n_taskruns = sqlio.read_sql_query(sql_n_taskruns, self.db.engine)
        n_pending_taskruns = sqlio.read_sql_query(sql_n_pending_taskruns, self.db.engine)
        project_details = sqlio.read_sql_query(sql_project_details, self.db.engine)
        worker_details = sqlio.read_sql_query(sql_worker_details, self.db.engine)

        # join data frames
        data = pd.DataFrame(project_details)
        data_frames = [completed_tasks, total_tasks, n_workers, worker_details,
            n_taskruns, n_pending_taskruns]
        for df in data_frames:
            data = pd.merge(data, df, on='project_id', how='left')

        # round up values
        data['n_tasks'].fillna(0, inplace=True)
        data['completed_tasks'].fillna(0, inplace=True)
        data['n_tasks'] = data['n_tasks'].astype(int)

        # compute percentage tasks complete
        data['percent_complete'] = 0
        data.loc[(data['n_tasks'] > 0) & (data['completed_tasks'] > 0), 'percent_complete'] = data['completed_tasks'] * 100 / data['n_tasks']
        data['percent_complete'] = data['percent_complete'].astype(int)

        # compute pending tasks
        data['n_pending_tasks'] = data['n_tasks'] - data['completed_tasks']

        # url column for each project
        data['url'] = base_url + data['short_name'].astype('unicode')

        # manage report columns; reorder
        data = data[[
            'project_id', 'name', 'url', 'short_name', 'long_description', 'created', 'owner_name',
            'owner_email', 'category_name', 'finish_time', 'percent_complete', 'n_tasks', 'n_pending_tasks',
            'n_workers', 'workers', 'updated', 'last_submission', 'n_taskruns', 'n_pending_taskruns']]
        return data
