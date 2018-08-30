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
"""Dashboard Jobs module for running background tasks in PYBOSSA server."""
from sqlalchemy import text
from pybossa.core import db


def _exists_materialized_view(view):
    sql = text('''SELECT EXISTS (
                SELECT relname
                FROM pg_catalog.pg_class c JOIN pg_namespace n
                ON n.oid = c.relnamespace
                WHERE c.relkind = 'm'
                AND n.nspname = current_schema()
                AND c.relname = :view);''')
    results = db.slave_session.execute(sql, dict(view=view))
    for result in results:
        return result.exists
    return False


def _refresh_materialized_view(view):
    sql = text('REFRESH MATERIALIZED VIEW %s' % view)
    db.session.execute(sql)
    db.session.commit()
    return "Materialized view refreshed"


def active_users_week():
    """Create or update active users last week materialized view."""
    if _exists_materialized_view('dashboard_week_users'):
        return _refresh_materialized_view('dashboard_week_users')
    else:
        sql = text('''CREATE MATERIALIZED VIEW dashboard_week_users AS
                   WITH crafters_per_day AS
                        (select to_date(task_run.finish_time,
                                        'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                                user_id, COUNT(task_run.user_id) AS day_crafters
                        FROM task_run
                        WHERE to_date(task_run.finish_time,
                                      'YYYY-MM-DD\THH24:MI:SS.US')
                            >= NOW() - ('1 week'):: INTERVAL
                        GROUP BY day, task_run.user_id)
                   SELECT day, COUNT(crafters_per_day.user_id) AS n_users
                   FROM crafters_per_day GROUP BY day ORDER BY day;''')
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"


def active_anon_week():
    """Create or update active anon last week materialized view."""
    if _exists_materialized_view('dashboard_week_anon'):
        return _refresh_materialized_view('dashboard_week_anon')
    else:
        sql = text('''CREATE MATERIALIZED VIEW dashboard_week_anon AS
                   WITH crafters_per_day AS
                        (select to_date(task_run.finish_time,
                                        'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                                user_ip, COUNT(task_run.user_ip) AS day_crafters
                        FROM task_run
                        WHERE to_date(task_run.finish_time,
                                      'YYYY-MM-DD\THH24:MI:SS.US')
                            >= NOW() - ('1 week'):: INTERVAL
                        GROUP BY day, task_run.user_ip)
                   SELECT day, COUNT(crafters_per_day.user_ip) AS n_users
                   FROM crafters_per_day GROUP BY day ORDER BY day;''')
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"


def draft_projects_week():
    """Create or update new created draft projects last week materialized view."""
    if _exists_materialized_view('dashboard_week_project_draft'):
        return _refresh_materialized_view('dashboard_week_project_draft')
    else:
        sql = text('''CREATE MATERIALIZED VIEW dashboard_week_project_draft AS
                   SELECT TO_DATE(project.created, 'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                   project.id, short_name, project.name,
                   owner_id, "user".name AS u_name, "user".email_addr
                   FROM project, "user"
                   WHERE TO_DATE(project.created,
                                'YYYY-MM-DD\THH24:MI:SS.US') >= now() -
                                ('1 week')::INTERVAL
                   AND "user".id = project.owner_id
                   AND "user".restrict = false
                   AND project.published = false
                   GROUP BY project.id, "user".name, "user".email_addr;''')
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"


def published_projects_week():
    """Create or update published projects last week materialized view."""
    if _exists_materialized_view('dashboard_week_project_published'):
        return _refresh_materialized_view('dashboard_week_project_published')
    else:
        sql = text('''CREATE MATERIALIZED VIEW dashboard_week_project_published AS
                   SELECT TO_DATE(auditlog.created, 'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                   project.id, project.short_name, project.name,
                   owner_id, "user".name AS u_name, "user".email_addr
                   FROM auditlog, project, "user"
                   WHERE TO_DATE(auditlog.created,
                                'YYYY-MM-DD\THH24:MI:SS.US') >= now() -
                                ('1 week')::INTERVAL
                   AND "user".id = project.owner_id
                   AND "user".restrict = false
                   AND project.owner_id = auditlog.user_id
                   AND auditlog.project_id = project.id
                   AND auditlog.attribute = 'published'
                   GROUP BY auditlog.id, "user".name, "user".email_addr, project.id;''')
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"


def update_projects_week():
    """Create or update updated projects last week materialized view."""
    if _exists_materialized_view('dashboard_week_project_update'):
        return _refresh_materialized_view('dashboard_week_project_update')
    else:
        sql = text('''CREATE MATERIALIZED VIEW dashboard_week_project_update AS
                   SELECT TO_DATE(project.updated, 'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                   project.id, short_name, project.name,
                   owner_id, "user".name AS u_name, "user".email_addr
                   FROM project, "user"
                   WHERE TO_DATE(project.updated,
                                'YYYY-MM-DD\THH24:MI:SS.US') >= now() -
                                ('1 week')::INTERVAL
                   AND "user".id = project.owner_id
                   AND "user".restrict = false
                   GROUP BY project.id, "user".name, "user".email_addr;''')
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"


def new_tasks_week():
    """Create or update new tasks last week materialized view."""
    if _exists_materialized_view('dashboard_week_new_task'):
        return _refresh_materialized_view('dashboard_week_new_task')
    else:
        sql = text('''CREATE MATERIALIZED VIEW dashboard_week_new_task AS
                      SELECT TO_DATE(task.created,
                                     'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                      COUNT(task.id) AS day_tasks
                      FROM task WHERE TO_DATE(task.created,
                                              'YYYY-MM-DD\THH24:MI:SS.US')
                                          >= now() - ('1 week'):: INTERVAL
                      GROUP BY day ORDER BY day ASC;''')
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"


def new_task_runs_week():
    """Create or update new task_runs last week materialized view."""
    if _exists_materialized_view('dashboard_week_new_task_run'):
        return _refresh_materialized_view('dashboard_week_new_task_run')
    else:
        sql = text('''CREATE MATERIALIZED VIEW dashboard_week_new_task_run AS
                      SELECT TO_DATE(task_run.finish_time,
                                     'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                      COUNT(task_run.id) AS day_task_runs
                      FROM task_run WHERE TO_DATE(task_run.finish_time,
                                              'YYYY-MM-DD\THH24:MI:SS.US')
                                          >= now() - ('1 week'):: INTERVAL
                      GROUP BY day;''')
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"


def new_users_week():
    """Create or update new users last week materialized view."""
    if _exists_materialized_view('dashboard_week_new_users'):
        return _refresh_materialized_view('dashboard_week_new_users')
    else:
        sql = text('''CREATE MATERIALIZED VIEW dashboard_week_new_users AS
                      SELECT TO_DATE("user".created,
                                     'YYYY-MM-DD\THH24:MI:SS.US') AS day,
                      COUNT("user".id) AS day_users
                      FROM "user" WHERE TO_DATE("user".created,
                                              'YYYY-MM-DD\THH24:MI:SS.US')
                                          >= now() - ('1 week'):: INTERVAL
                      AND "user".restrict=false
                      GROUP BY day;''')
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"


def returning_users_week():
    """Create or update returning users last week materialized view."""
    if _exists_materialized_view('dashboard_week_returning_users'):
        return _refresh_materialized_view('dashboard_week_returning_users')
    else:
        sql = text('''CREATE MATERIALIZED VIEW dashboard_week_returning_users AS
                   WITH data AS (
                    SELECT user_id, TO_DATE(task_run.finish_time,
                    'YYYY-MM-DD\THH24:MI:SS.US') AS day
                   FROM task_run
                   WHERE TO_DATE(task_run.finish_time,
                   'YYYY-MM-DD\THH24:MI:SS.US') >= NOW()
                   - ('1 week')::INTERVAL GROUP BY day, task_run.user_id)
                   SELECT user_id, COUNT(user_id) AS n_days
                   FROM data GROUP BY user_id HAVING(count(user_id) > 1)
                   ORDER by n_days;
                      ''')
        db.session.execute(sql)
        db.session.commit()
        return "Materialized view created"
