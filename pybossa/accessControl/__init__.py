#myKaarma

from sqlalchemy.exc import IntegrityError
from sqlalchemy import cast, Date
from pybossa.model.project import Project
from pybossa.core import project_repo
from sqlalchemy import text
from pybossa.core import db


def authority_check(user_id,resource_id,resource_type,operation):
    sql = '''
            SELECT user_authorities.id
            FROM user_authorities where user_id= {} and resource_id = {} and resource_type = '{}' and operation = '{}';
            '''.format(user_id,resource_id,resource_type,operation)
    try:
        res = db.session.execute(sql)
        for row in res:
            return True
        return False
    except SQLAlchemyError as e:
        return False

def authority_check_admin(user_id,operation):
    sql = '''
            SELECT user_authorities.id
            FROM user_authorities where user_id= {} and operation = '{}';
            '''.format(user_id,operation)
    try:
        res = db.session.execute(sql)
        for row in res:
            return True
        return False
    except SQLAlchemyError as e:
        return False


    