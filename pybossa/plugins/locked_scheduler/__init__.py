import pybossa.sched as sched
from pybossa.forms.forms import TaskSchedulerForm
from flask.ext.plugins import Plugin
from flask.ext.login import current_user
from flask import request
from sqlalchemy.sql import text
from functools import wraps
from redis_lock import LockManager
from pybossa.core import sentinel
from pybossa.core import project_repo
from pybossa.api.task_run import TaskRunAPI
from pybossa.auth.task import TaskAuth
from pybossa.contributions_guard import ContributionsGuard
from pybossa.error import ErrorStatus
from werkzeug.exceptions import BadRequest
import json

__plugin__ = "LockedScheduler"
__version__ = "0.0.1"

SCHEDULER_NAME = "locked_scheduler"
SCHEDULER_DISPLAY_NAME = "Locked Scheduler"

TIMEOUT = ContributionsGuard.STAMP_TTL
KEY_PREFIX = "pybossa:project:task_requested:timestamps:{0}:{1}"

session = sched.session


def get_task(project_id, user_id=None, user_ip=None,
             external_uid=None, offset=0):
    """Add here the logic for your scheduler."""
    if offset > 2:
        raise BadRequest
    sql = text('''
           SELECT task.id, COUNT(task_run.task_id) AS taskcount, n_answers
           FROM task
           LEFT JOIN task_run ON (task.id = task_run.task_id)
           WHERE NOT EXISTS
           (SELECT 1 FROM task_run WHERE project_id=:project_id AND
           user_id=:user_id AND task_id=task.id)
           AND task.project_id=:project_id AND task.state !='completed'
           group by task.id ORDER BY priority_0 DESC, id ASC LIMIT 10;
           ''')
    rows = session.execute(sql, dict(project_id=project_id, user_id=user_id))

    redis_conn = sentinel.master
    lock_manager = LockManager(redis_conn, TIMEOUT)

    skipped = 0
    for task_id, count, n_answer in rows:
        key = KEY_PREFIX.format(project_id, task_id)
        if lock_manager.acquire_lock(key, user_id, n_answer - count):
            if skipped == offset:
                return session.query(sched.Task).get(task_id)
            else:
                skipped += 1
    return None


def with_custom_scheduler(f):
    @wraps(f)
    def wrapper(project_id, sched, user_id=None,
                user_ip=None, external_uid=None, offset=0):
        if sched == SCHEDULER_NAME:
            return get_task(project_id, user_id, user_ip,
                            external_uid, offset=offset)
        return f(project_id, sched, user_id=user_id, user_ip=user_ip,
                 external_uid=external_uid, offset=offset)
    return wrapper


def variants_with_custom_scheduler(f):
    @wraps(f)
    def wrapper():
        return f() + [(SCHEDULER_NAME, SCHEDULER_DISPLAY_NAME)]
    return wrapper


def with_task_lock_check(f):
    @wraps(f)
    def wrapper(self):
        ret_val = f(self)
        project_id, task_id, user_id = get_task_run_info()
        sched = get_project_scheduler(project_id)
        is_error = isinstance(ret_val, ErrorStatus)
        if sched == SCHEDULER_NAME and not is_error:
            key = KEY_PREFIX.format(project_id, task_id)
            redis_conn = sentinel.master
            lock_manager = LockManager(redis_conn, TIMEOUT)
            lock_manager.release_lock(key, user_id)
        return ret_val
    return wrapper


def with_read_auth(f):
    """
    Wrap TaskAuth._read to disallow direct access to
    a particular task unless the user already has locked it
    """
    redis_conn = sentinel.master
    lock_manager = LockManager(redis_conn, TIMEOUT)

    @wraps(f)
    def wrapper(self, user, task):
        if task is not None:
            project_id = task.project_id
            task_id = task.id
            scheduler = get_project_scheduler(project_id)
            if scheduler == SCHEDULER_NAME:
                key = KEY_PREFIX.format(project_id, task_id)
                return lock_manager.has_lock(key, user.id)
        return f(self, user, task)

    return wrapper


def get_task_run_info():
    if "request_json" in request.form:
        data = json.loads(request.form["request_json"])
    else:
        data = json.loads(request.data)
    project_id = data["project_id"]
    task_id = data["task_id"]
    user_id = current_user.id
    return project_id, task_id, user_id


def get_project_scheduler(project_id):
    project = project_repo.get(project_id)
    return project.info.get("sched")


class LockedScheduler(Plugin):

    def setup(self):
        sched.new_task = with_custom_scheduler(sched.new_task)
        sched.sched_variants = variants_with_custom_scheduler(sched.sched_variants)
        TaskSchedulerForm.update_sched_options(sched.sched_variants())

        # add lock check to task_run api
        TaskRunAPI.post = with_task_lock_check(TaskRunAPI.post)
        TaskAuth._read = with_read_auth(TaskAuth._read)
