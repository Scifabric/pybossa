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
from werkzeug.exceptions import BadRequest, Forbidden
import json

__plugin__ = "LockedScheduler"
__version__ = "0.0.1"

SCHEDULER_NAME = "locked_scheduler"
SCHEDULER_DISPLAY_NAME = "Locked Scheduler"

TIMEOUT = ContributionsGuard.STAMP_TTL
KEY_PREFIX = "pybossa:project:task_requested:timestamps:{0}:{1}"

session = sched.session
error = ErrorStatus()


def get_new_task(project_id, user_id=None, user_ip=None,
                 external_uid=None, offset=0):
    """
    Select a new task to be returned to the contributor. For each incomplete
    task, check if the number of users working on the task is smaller than the
    number of answers still needed. In that case, acquire a lock on the task
    and return the task to the user. If offset is nonzero, skip that amount
    of available tasks before returning to the user.
    """
    if offset > 2:
        raise BadRequest()
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

    skipped = 0
    for task_id, taskcount, n_answers in rows:
        remaining = n_answers - taskcount
        if acquire_lock(project_id, task_id, user_id, remaining):
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
            return get_new_task(project_id, user_id, user_ip,
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
    """
    Wrap the post method for TaskRunApi. If the scheduler is set, check
    if the user holds a lock before submitting the task. Release the lock
    if the task is submitted successfully
    """
    @wraps(f)
    def wrapper(self):
        project_id, task_id, user_id = get_task_run_info()
        scheduler = get_project_scheduler(project_id)
        if scheduler != SCHEDULER_NAME:
            return f(self)
        try:
            return _locked_post(f, self, project_id, task_id, user_id)
        except Exception as e:
            return error.format_exception(
                e,
                target=self.__class__.__name__.lower(),
                action='POST'
            )
    return wrapper


def _locked_post(f, self, project_id, task_id, user_id):
    if not has_lock(project_id, task_id, user_id):
        raise Forbidden('You must request a task first!')
    ret_val = f(self)
    if not isinstance(ret_val, ErrorStatus):
        release_lock(project_id, task_id, user_id)
    return ret_val


def with_read_auth(f):
    """
    Wrap TaskAuth._read to disallow direct access to a particular
    task unless the user already has locked it (or is an admin)
    """
    @wraps(f)
    def wrapper(self, user, task):
        if task is not None:
            project_id = task.project_id
            task_id = task.id
            scheduler = get_project_scheduler(project_id)
            if scheduler == SCHEDULER_NAME:
                is_admin = not user.is_anonymous() and user.admin
                return is_admin or has_lock(project_id, task_id, user.id)
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


def has_lock(project_id, task_id, user_id):
    lock_manager = LockManager(sentinel.master, TIMEOUT)
    key = get_key(project_id, task_id)
    return lock_manager.has_lock(key, user_id)


def acquire_lock(project_id, task_id, user_id, limit):
    lock_manager = LockManager(sentinel.master, TIMEOUT)
    key = get_key(project_id, task_id)
    return lock_manager.acquire_lock(key, user_id, limit)


def release_lock(project_id, task_id, user_id):
    lock_manager = LockManager(sentinel.master, TIMEOUT)
    key = get_key(project_id, task_id)
    lock_manager.release_lock(key, user_id)


def get_key(project_id, task_id):
    return KEY_PREFIX.format(project_id, task_id)


class LockedScheduler(Plugin):

    def setup(self):
        sched.new_task = with_custom_scheduler(sched.new_task)
        sched.sched_variants = variants_with_custom_scheduler(sched.sched_variants)
        TaskSchedulerForm.update_sched_options(sched.sched_variants())

        # add lock check to task_run api
        TaskRunAPI.post = with_task_lock_check(TaskRunAPI.post)
        TaskAuth._read = with_read_auth(TaskAuth._read)
