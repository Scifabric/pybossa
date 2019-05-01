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

from pybossa.repositories import Repository
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model import make_timestamp
from pybossa.model.user import User
from pybossa.exc import WrongObjectError, DBIntegrityError
from pybossa.cache import projects as cached_projects
from pybossa.core import uploader
from sqlalchemy import text
from pybossa.cache.task_browse_helpers import get_task_filters
import json
from datetime import datetime, timedelta
from flask import current_app
from pybossa.data_access import ensure_task_assignment_to_project
from sqlalchemy import or_


class TaskRepository(Repository):
    MIN_REDUNDANCY = 1
    MAX_REDUNDANCY = 1000
    SAVE_ACTION = 'saved'
    UPDATE_ACTION = 'updated'

    # Methods for queries on Task objects
    def get_task(self, id):
        return self.db.session.query(Task).get(id)

    def get_task_by(self, **attributes):
        filters, _, _, _ = self.generate_query_from_keywords(Task, **attributes)
        return self.db.session.query(Task).filter(*filters).first()

    def filter_tasks_by(self, limit=None, offset=0, yielded=False,
                        last_id=None, fulltextsearch=None, desc=False,
                        **filters):

        return self._filter_by(Task, limit, offset, yielded, last_id,
                              fulltextsearch, desc, **filters)

    def filter_completed_tasks_gold_tasks_by(self, limit=None, offset=0,
        last_id=None, yielded=False, desc=False, **filters):

        exp = filters.pop('exported', None)
        filters.pop('state', None) # exclude state param
        if exp is not None:
            query = self.db.session.query(Task).\
                filter(or_(Task.state == u'completed', Task.calibration == 1)).\
                filter(Task.exported == exp).\
                filter_by(**filters)
        else:
            query = self.db.session.query(Task).\
                filter(or_(Task.state == u'completed', Task.calibration == 1)).\
                filter_by(**filters)

        results = self._filter_query(query, Task, limit, offset, last_id, yielded, desc)
        return results

    def filter_completed_taskruns_gold_taskruns_by(self, limit=None, offset=0,
        last_id=None, yielded=False, desc=False, **filters):

        exp = filters.pop('exported', None)
        finish_time = filters.pop('finish_time', None)
        filters.pop('state', None) # exclude state param

        conditions = []
        if exp:
            conditions.append(Task.exported == exp)
        if finish_time:
            conditions.append(TaskRun.finish_time >= finish_time)

        query = self.db.session.query(TaskRun).join(Task).\
            filter(TaskRun.task_id == Task.id).\
            filter(or_(Task.state == u'completed', Task.calibration == 1)).\
            filter(*conditions).\
            filter_by(**filters)

        results = self._filter_query(query, Task, limit, offset, last_id, yielded, desc)
        return results

    def get_gold_task_count_for_project(self, project_id):
        return (self.db.session.query(Task)
                .filter(Task.project_id == project_id)
                .filter(Task.calibration == 1)
                .count())

    def count_tasks_with(self, **filters):
        query_args, _, _, _  = self.generate_query_from_keywords(Task, **filters)
        return self.db.session.query(Task).filter(*query_args).count()

    def filter_tasks_by_user_favorites(self, uid, **filters):
        """Return tasks marked as favorited by user.id."""
        query = self.db.session.query(Task).filter(Task.fav_user_ids.any(uid))
        limit = filters.get('limit', 20)
        offset = filters.get('offset', 0)
        last_id = filters.get('last_id', None)
        desc = filters.get('desc', False)
        orderby = filters.get('orderby', 'id')
        if last_id:
            query = query.filter(Task.id > last_id)
        query = self._set_orderby_desc(query, Task, limit,
                                       last_id, offset,
                                       desc, orderby)
        return query.all()

    def get_task_favorited(self, uid, task_id):
        """Return task marked as favorited by user.id."""
        tasks = self.db.session.query(Task)\
                    .filter(Task.fav_user_ids.any(uid),
                            Task.id==task_id)\
                    .all()
        return tasks

    # Methods for queries on TaskRun objects
    def get_task_run(self, id):
        return self.db.session.query(TaskRun).get(id)

    def get_task_run_by(self, fulltextsearch=None, **attributes):
        filters, _, _, _  = self.generate_query_from_keywords(TaskRun,
                                                    fulltextsearch,
                                                    **attributes)
        return self.db.session.query(TaskRun).filter(*filters).first()

    def filter_task_runs_by(self, limit=None, offset=0, last_id=None,
                            yielded=False, fulltextsearch=None,
                            desc=False, **filters):
        return self._filter_by(TaskRun, limit, offset, yielded, last_id,
                              fulltextsearch, desc, **filters)

    def count_task_runs_with(self, **filters):
        query_args, _, _, _ = self.generate_query_from_keywords(TaskRun, **filters)
        return self.db.session.query(TaskRun).filter(*query_args).count()

    def get_user_has_task_run_for_project(self, project_id, user_id):
        return (self.db.session.query(TaskRun)
                .filter(TaskRun.user_id == user_id)
                .filter(TaskRun.project_id == project_id)
                .first()) is not None

    # Filter helpers
    def _filter_query(self, query, obj, limit, offset, last_id, yielded, desc):
        if last_id:
            query = query.filter(obj.id > last_id)
            query = query.order_by(obj.id).limit(limit)
        else:
            if desc:
                query = query.order_by(cast(obj.created, Date).desc())\
                        .limit(limit).offset(offset)
            else:
                query = query.order_by(obj.id).limit(limit).offset(offset)
        if yielded:
            limit = limit or 1
            return query.yield_per(limit)
        return query.all()


    # Methods for saving, deleting and updating both Task and TaskRun objects
    def save(self, element):
        self._validate_can_be(self.SAVE_ACTION, element)
        try:
            self.db.session.add(element)
            self.db.session.commit()
            cached_projects.clean_project(element.project_id)
        except IntegrityError as e:
            self.db.session.rollback()
            raise DBIntegrityError(e)

    def update(self, element):
        self._validate_can_be(self.UPDATE_ACTION, element)
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

    def delete_task_by_id(self, project_id, task_id):
        args = dict(project_id=project_id, task_id=task_id)
        self.db.session.execute(text('''
                   DELETE FROM result WHERE project_id=:project_id
                                      AND task_id=:task_id;'''), args)
        self.db.session.execute(text('''
                   DELETE FROM task_run WHERE project_id=:project_id
                                        AND task_id=:task_id;'''), args)
        self.db.session.execute(text('''
                   DELETE FROM task WHERE project_id=:project_id
                                    AND id=:task_id;'''), args)
        self.db.session.commit()
        cached_projects.clean(project_id)

    def delete_valid_from_project(self, project, force_reset=False, filters=None):
        if not force_reset:
            """Delete only tasks that have no results associated."""
            params = {}
            sql = text('''
                DELETE FROM task WHERE task.project_id=:project_id
                AND task.id NOT IN
                (SELECT task_id FROM result
                WHERE result.project_id=:project_id GROUP BY result.task_id);
                ''')
        else:
            """force reset, remove all results."""
            filters = filters or {}
            conditions, params = get_task_filters(filters)

            # bulkdel db conn is with db user having session_replication_role
            # when bulkdel is not configured, make explict sql query to set
            # session replication role to replica
            sql_session_repl = ''
            if not 'bulkdel' in current_app.config.get('SQLALCHEMY_BINDS'):
                sql_session_repl = 'SET session_replication_role TO replica;'
            sql = text('''
                BEGIN;

                {}

                CREATE TEMP TABLE to_delete ON COMMIT DROP AS (
                    SELECT task.id as id,
                    coalesce(ct, 0) as n_task_runs, task.n_answers, ft,
                    priority_0, task.created
                    FROM task LEFT OUTER JOIN
                    (SELECT task_id, CAST(COUNT(id) AS FLOAT) AS ct,
                    MAX(finish_time) as ft FROM task_run
                    WHERE project_id=:project_id GROUP BY task_id) AS log_counts
                    ON task.id=log_counts.task_id
                    WHERE task.project_id=:project_id {}
                );
                DELETE FROM result WHERE project_id=:project_id
                       AND task_id in (SELECT id FROM to_delete);
                DELETE FROM task_run WHERE project_id=:project_id
                       AND task_id in (SELECT id FROM to_delete);
                DELETE FROM task WHERE task.project_id=:project_id
                       AND id in (SELECT id FROM to_delete);
                COMMIT;
                '''.format(sql_session_repl, conditions))
        self.db.bulkdel_session.execute(sql, dict(project_id=project.id, **params))
        self.db.bulkdel_session.commit()
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

    def update_tasks_redundancy(self, project, n_answers, filters=None):
        """
        Update the n_answer of every task from a project and their state.
        Use raw SQL for performance. Mark tasks as exported = False for
        tasks with curr redundancy < new redundancy, with state as completed
        and were marked as exported = True
        """

        if n_answers < self.MIN_REDUNDANCY or n_answers > self.MAX_REDUNDANCY:
            raise ValueError("Invalid redundancy value: {}".format(n_answers))

        filters = filters or {}
        task_expiration = '{} day'.format(self.rdancy_upd_exp)
        conditions, params = get_task_filters(filters)
        tasks_not_updated = self._get_redundancy_update_msg(
            project, n_answers, conditions, params, task_expiration)

        self.update_task_exported_status(project.id, n_answers, conditions, params, task_expiration)
        sql = text('''
                   WITH all_tasks_with_orig_filter AS (
                        SELECT task.id as id,
                        coalesce(ct, 0) as n_task_runs, task.n_answers, ft,
                        priority_0, task.created
                        FROM task LEFT OUTER JOIN
                        (SELECT task_id, CAST(COUNT(id) AS FLOAT) AS ct,
                        MAX(finish_time) as ft FROM task_run
                        WHERE project_id=:project_id GROUP BY task_id) AS log_counts
                        ON task.id=log_counts.task_id
                        WHERE task.project_id=:project_id {}
                   ),

                   tasks_with_file_urls AS (
                        SELECT t.id as id FROM task t
                        WHERE t.id IN (SELECT id from all_tasks_with_orig_filter)
                        AND jsonb_typeof(t.info) = 'object'
                        AND EXISTS(SELECT TRUE FROM jsonb_object_keys(t.info) AS key
                        WHERE key ILIKE '%\_\_upload\_url%')
                   ),

                   tasks_excl_file_urls AS (
                        SELECT id FROM all_tasks_with_orig_filter
                        WHERE id NOT IN (SELECT id FROM tasks_with_file_urls)
                   )

                   UPDATE task SET n_answers=:n_answers,
                   state='ongoing' WHERE project_id=:project_id AND
                   ((id IN (SELECT id from tasks_excl_file_urls)) OR
                   (id IN (SELECT id from tasks_with_file_urls) AND state='ongoing'
                   AND TO_DATE(created, 'YYYY-MM-DD\THH24:MI:SS.US') >= NOW() - :task_expiration ::INTERVAL));'''
                   .format(conditions))
        self.db.session.execute(sql, dict(n_answers=n_answers,
                                          project_id=project.id,
                                          task_expiration=task_expiration,
                                          **params))
        self.update_task_state(project.id)
        self.db.session.commit()
        cached_projects.clean_project(project.id)
        return tasks_not_updated

    def update_task_state(self, project_id):
        # Create temp tables for completed tasks
        sql = text('''
                   CREATE TEMP TABLE complete_tasks ON COMMIT DROP AS (
                   SELECT task.id, array_agg(task_run.id) as task_runs
                   FROM task, task_run
                   WHERE task_run.task_id=task.id
                   AND task.project_id=:project_id
                   AND task.calibration!=1
                   GROUP BY task.id
                   having COUNT(task_run.id) >= task.n_answers);
                   ''')
        self.db.session.execute(sql, dict(project_id=project_id))
        # Set state to completed
        sql = text('''
                   UPDATE task SET state='completed'
                   FROM complete_tasks
                   WHERE complete_tasks.id=task.id;
                   ''')
        self.db.session.execute(sql)

        sql = text('''
                   INSERT INTO result
                   (created, project_id, task_id, task_run_ids, last_version) (
                   SELECT :ts, :project_id, completed_no_results.id,
                          completed_no_results.task_runs, true
                   FROM ( SELECT task.id as id,
                          array_agg(task_run.id) as task_runs
                          FROM task, task_run
                          WHERE task.state = 'completed'
                          AND task_run.task_id = task.id
                          AND NOT EXISTS (SELECT 1 FROM result
                                          WHERE result.task_id = task.id)
                          AND task.project_id=:project_id
                          GROUP BY task.id
                        ) as completed_no_results
                   );''')
        self.db.session.execute(sql, dict(project_id=project_id,
                                          ts=make_timestamp()))

    def update_priority(self, project_id, priority, filters):
        priority = min(1.0, priority)
        priority = max(0.0, priority)
        conditions, params = get_task_filters(filters)
        sql = text('''
                   WITH to_update AS (
                        SELECT task.id as id,
                        coalesce(ct, 0) as n_task_runs, task.n_answers, ft,
                        priority_0, task.created
                        FROM task LEFT OUTER JOIN
                        (SELECT task_id, CAST(COUNT(id) AS FLOAT) AS ct,
                        MAX(finish_time) as ft FROM task_run
                        WHERE project_id=:project_id GROUP BY task_id) AS log_counts
                        ON task.id=log_counts.task_id
                        WHERE task.project_id=:project_id {}
                   )
                   UPDATE task
                   SET priority_0=:priority
                   WHERE project_id=:project_id AND task.id in (
                        SELECT id FROM to_update);
                   '''.format(conditions))
        self.db.session.execute(sql, dict(priority=priority,
                                          project_id=project_id,
                                          **params))
        self.db.session.commit()
        cached_projects.clean_project(project_id)

    def find_duplicate(self, project_id, info):
        """
        Find a task id in the given project with the project info using md5
        index on info column casted as text. Md5 is used to avoid key size
        limitations in BTree indices
        """
        sql = text('''
                   SELECT task.id as task_id
                   FROM task
                   WHERE task.project_id=:project_id
                   AND task.state='ongoing'
                   AND md5(task.info::text)=md5(((:info)::jsonb)::text)
                   ''')
        info = json.dumps(info, allow_nan=False)
        row = self.db.session.execute(
            sql, dict(info=info, project_id=project_id)).first()
        if row:
            return row[0]

    def _validate_can_be(self, action, element):
        from flask import current_app
        from pybossa.core import project_repo
        if not isinstance(element, Task) and not isinstance(element, TaskRun):
            name = element.__class__.__name__
            msg = '%s cannot be %s by %s' % (name, action, self.__class__.__name__)
            raise WrongObjectError(msg)
        if isinstance(element, Task) and (action in [self.SAVE_ACTION, self.UPDATE_ACTION]):
            project = project_repo.get(element.project_id)
            ensure_task_assignment_to_project(element, project)

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

    def update_task_exported_status(self, project_id, n_answers, conditions, params, task_expiration):
        """
        Update exported=False for completed tasks that were exported
        and with new redundancy, they'll be marked as ongoing
        """
        sql = text('''
                   WITH all_tasks_with_orig_filter AS (
                        SELECT task.id as id,
                        coalesce(ct, 0) as n_task_runs, task.n_answers, ft,
                        priority_0, task.created
                        FROM task LEFT OUTER JOIN
                        (SELECT task_id, CAST(COUNT(id) AS FLOAT) AS ct,
                        MAX(finish_time) as ft FROM task_run
                        WHERE project_id=:project_id GROUP BY task_id) AS log_counts
                        ON task.id=log_counts.task_id
                        WHERE task.project_id=:project_id
                        AND task.state='completed'
                        AND task.n_answers < :n_answers {}
                   ),

                   tasks_with_file_urls AS (
                        SELECT t.id as id FROM task t
                        WHERE t.id IN (SELECT id from all_tasks_with_orig_filter)
                        AND jsonb_typeof(t.info) = 'object'
                        AND EXISTS(SELECT TRUE FROM jsonb_object_keys(t.info) AS key
                        WHERE key ILIKE '%\_\_upload\_url%')
                   ),

                   tasks_excl_file_urls AS (
                        SELECT id FROM all_tasks_with_orig_filter
                        WHERE id NOT IN (SELECT id FROM tasks_with_file_urls)
                   )

                   UPDATE task SET exported=False
                   WHERE project_id=:project_id AND
                   ((id IN (SELECT id from tasks_excl_file_urls)) OR
                   (id IN (SELECT id from tasks_with_file_urls) AND state='ongoing'
                   AND TO_DATE(created, 'YYYY-MM-DD\THH24:MI:SS.US') >= NOW() - :task_expiration ::INTERVAL));'''
                   .format(conditions))
        self.db.session.execute(sql, dict(n_answers=n_answers,
                                          project_id=project_id,
                                          task_expiration=task_expiration,
                                          **params))


    def _get_redundancy_update_msg(self, project, n_answers, conditions, params, task_expiration):
        sql = text('''
                   WITH all_tasks_with_orig_filter AS (
                        SELECT task.id as id,
                        coalesce(ct, 0) as n_task_runs, task.n_answers, ft,
                        priority_0, task.created
                        FROM task LEFT OUTER JOIN
                        (SELECT task_id, CAST(COUNT(id) AS FLOAT) AS ct,
                        MAX(finish_time) as ft FROM task_run
                        WHERE project_id=:project_id GROUP BY task_id) AS log_counts
                        ON task.id=log_counts.task_id
                        WHERE task.project_id=:project_id {}
                   )

                   SELECT t.id as id FROM task t
                   WHERE t.id IN (SELECT id from all_tasks_with_orig_filter)
                   AND jsonb_typeof(t.info) = 'object'
                   AND EXISTS(SELECT TRUE FROM jsonb_object_keys(t.info) AS key
                   WHERE key ILIKE '%\_\_upload\_url%')
                   AND (t.state = 'completed' OR TO_DATE(created, 'YYYY-MM-DD\THH24:MI:SS.US') < NOW() - :task_expiration ::INTERVAL)
                   AND n_answers != :n_answers;'''
                   .format(conditions))
        tasks = self.db.session.execute(sql,
            dict(project_id=project.id, n_answers=n_answers,
            task_expiration=task_expiration, **params)).fetchall()
        tasks_not_updated = '\n'.join([str(task.id) for task in tasks])
        return tasks_not_updated
