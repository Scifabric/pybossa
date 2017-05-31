# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2017 SciFabric LTD.
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
"""Exporter module helper functions."""
from sqlalchemy.sql import text
from pybossa.core import db
from pybossa.model.project import Project
from pybossa.cache.task_browse_helpers import get_task_filters


session = db.slave_session


def browse_tasks_export(obj, project_id, expanded, **args):
    """Export tasks from the browse tasks view for a project
    using the same filters that are selected by the user
    in the UI.
    """
    filters, filter_params = get_task_filters(args)
    if obj == 'tasks':
        sql = text('''
                   SELECT *
                        , coalesce(ct, 0) as n_task_runs
                     FROM task
                     LEFT OUTER JOIN (
                       SELECT task_id
                            , CAST(COUNT(id) AS FLOAT) AS ct
                            , MAX(finish_time) as ft
                         FROM task_run
                           WHERE project_id=:project_id
                           GROUP BY task_id
                     ) AS log_counts
                    ON task.id=log_counts.task_id
                    WHERE project_id = :project_id
                    {}'''.format(filters)
                  )
    elif obj == 'taskruns':
        if expanded:
           sql = text('''
                      SELECT task_run.*
                           , task.*
                           , users.*
                        FROM task_run
                        LEFT OUTER JOIN (
                          SELECT task.*
                            FROM task
                            WHERE project_id = :project_id
                          ) AS task
                        ON task_run.task_id = task.id
                        LEFT OUTER JOIN (
                          SELECT task_id
                               , CAST(COUNT(id) AS FLOAT) AS ct
                               , MAX(finish_time) as ft
                            FROM task_run
                              WHERE project_id = :project_id
                              GROUP BY task_id
                        ) AS log_counts
                        ON task.id=log_counts.task_id
                        LEFT OUTER JOIN (
                          SELECT *
                            FROM "user"
                          ) as users
                        ON task_run.user_id = users.id
                        WHERE task_run.project_id = :project_id
                        {}'''.format(filters)
                     )
        else:
           sql = text('''
                      SELECT task_run.*
                        FROM task_run
                        LEFT JOIN (
                          SELECT task.*
                            FROM task
                            WHERE project_id = :project_id
                          ) AS task
                        ON task_run.task_id = task.id
                        LEFT OUTER JOIN (
                          SELECT task_id
                               , CAST(COUNT(id) AS FLOAT) AS ct
                               , MAX(finish_time) as ft
                            FROM task_run
                              WHERE project_id=:project_id
                              GROUP BY task_id
                        ) AS log_counts
                        ON task.id = log_counts.task_id
                        WHERE task_run.project_id = :project_id
                        {}'''.format(filters)
                     )
    else:
        return

    results = session.execute(sql, dict(project_id=project_id, **filter_params))
    return results


