from pybossa.core import db, project_repo, task_repo

def mark_if_complete(task_id, project_id):
    project = project_repo.get(project_id)
    task = task_repo.get_task(task_id)
    # gold tasks never complete
    if task and task.calibration == 1:
        return

    if is_task_completed(task_id):
        update_task_state(task_id)


def is_task_completed(task_id):
    sql_query = ('select count(id) from task_run \
                 where task_run.task_id=:task_id')
    n_answers = db.session.scalar(sql_query, dict(task_id=task_id))
    sql_query = ('select n_answers from task \
                 where task.id=:task_id')
    task_n_answers = db.session.scalar(sql_query, dict(task_id=task_id))
    return n_answers >= task_n_answers


def update_task_state(task_id):
    sql_query = ("UPDATE task SET state='completed' \
                 where id = :task_id")
    db.session.execute(sql_query, dict(task_id=task_id))
    db.session.commit()
