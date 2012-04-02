from flaskext.login import current_user

def create(taskrun=None):
    return True

def read(taskrun=None):
    return True

def update(taskrun):
    if not current_user.is_anonymous() and taskrun.user != None:
        if taskrun.user.id == current_user.id:
            return True
        else:
            return False
    else:
        return False

def delete(app):
    return update(app)

