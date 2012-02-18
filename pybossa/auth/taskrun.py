from flaskext.login import current_user

def create(taskrun=None):
    return True

def read(taskrun=None):
    return True

def update(taskrun):
    if not current_user.is_anonymous() and taskrun.user == current_user:
        return True
    else:
        return False

def delete(app):
    return update(app)

