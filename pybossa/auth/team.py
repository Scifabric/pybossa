from flask.ext.login import current_user

def create(team=None):
    return not current_user.is_anonymous()

def read(team=None):
    return True

def update(team):
    if not current_user.is_anonymous() and (team.owner_id == current_user.id
                                            or current_user.admin is True):
        return True
    else:
        return False

def delete(team):
    return update(team)
