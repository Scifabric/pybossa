from flaskext.login import current_user
import pybossa.model as model
from pybossa.core import db


def create(task=None):
    if not current_user.is_anonymous():
        app = db.session.query(model.App).filter_by(id=task.app_id).one()
        if app.owner_id == current_user.id or current_user.admin is True:
            return True
        else:
            return False
    else:
        return False


def read(task=None):
    return True


def update(task):
    if not current_user.is_anonymous():
        app = db.session.query(model.App).filter_by(id=task.app_id).one()
        if app.owner_id == current_user.id or current_user.admin is True:
            return True
        else:
            return False
    else:
        return False


def delete(task):
    return update(task)
