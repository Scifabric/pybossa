from flaskext.login import current_user

def create(task=None):
    return not current_user.is_anonymous() 

def read(task=None):
    return True

def update(task):
    if not current_user.is_anonymous() and task.app.owner == current_user:
        return True
    else:
        return False

def delete(app):
    return update(app)

