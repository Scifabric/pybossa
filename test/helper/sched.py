from helper import web
from base import model, db


class Helper(web.Helper):
    """Class to help testing the scheduler"""
    def is_task(self, task_id, tasks):
        """Returns True if the task_id is in tasks list"""
        for t in tasks:
            if t.id == task_id:
                return True
        return False

    def is_unique(self, id, items):
        """Returns True if the id is not Unique"""
        copies = 0
        for i in items:
            if type(i) is dict:
                if i['id'] == id:
                    copies = copies + 1
            else:
                if i.id == id:
                    copies = copies + 1
        if copies >= 2:
            return False
        else:
            return True

    def del_task_runs(self, app_id=1):
        """Deletes all TaskRuns for a given app_id"""
        db.session.query(model.TaskRun).filter_by(app_id=1).delete()
        db.session.commit()
        db.session.remove()
