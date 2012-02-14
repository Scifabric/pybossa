from flaskext.login import current_user

def create():
    if current_user.is_anonymous(): return False
    else: return True

def read():
    return True

def update(app):
    if not current_user.is_anonymous():
        if app.owner_id == current_user.id:
            return True
        else: return False
    else: return False

def delete(app):
    return update(app)
