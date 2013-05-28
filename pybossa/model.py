# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

#import os
#from glob import iglob
import logging
import datetime
#import time
import json
import uuid

from werkzeug import generate_password_hash, check_password_hash
import flaskext.login
from sqlalchemy import BigInteger, Integer, Boolean, Unicode,\
        Float, UnicodeText, Text, String
from sqlalchemy.schema import Table, MetaData, Column, ForeignKey
from sqlalchemy.orm import relationship, backref, class_mapper
from sqlalchemy.types import MutableType, TypeDecorator
from sqlalchemy import event, text

from pybossa.core import db
from pybossa.util import pretty_date

log = logging.getLogger(__name__)

#Session = db.session

def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()

def make_uuid():
    return str(uuid.uuid4())


def rebuild_db():
    db.drop_all()
    db.create_all()

# =========================================
# Basics


class JSONType(MutableType, TypeDecorator):
    '''Additional Database Type for handling JSON values.
    '''
    impl = Text

    def __init__(self):
        super(JSONType, self).__init__()

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialiect):
        return json.loads(value)

    def copy_value(self, value):
        return json.loads(json.dumps(value))


class StateEnum:
    '''When creating  a task, the task can have the following states::

       * ALL: First time created
       * IN_PROGRESS:  The task is being run by one user
       * PENDING: The task has been completed but need to be validated
       * VALID: The task has been completed and validated
       * INVALID: The task has been complete but it is invalid
       * ERROR: The task has an error
    '''
    ALL = u'all'
    IN_PROGRESS = u'in_progress'
    PENDING = u'pending'
    VALID = u'valid'
    INVALID = u'invalid'
    ERROR = u'error'


class DomainObject(object):

    def dictize(self):
        out = {}
        for col in self.__table__.c:
            out[col.name] = getattr(self, col.name)
        return out

    @classmethod
    def undictize(cls, dict_):
        raise NotImplementedError()

    def __str__(self):
        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        repr = u'<%s' % self.__class__.__name__
        table = class_mapper(self.__class__).mapped_table
        for col in table.c:
            try:
                repr += u' %s=%s' % (col.name, getattr(self, col.name))
            except Exception, inst:
                repr += u' %s=%s' % (col.name, inst)

        repr += '>'
        return repr


# =========================================
# Domain Objects

class App(db.Model, DomainObject):
    '''A microtasking Application to which Tasks are associated.
    '''
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.id)

    __tablename__ = 'app'
    #: Unique id for this app (autogenerated)
    id = Column(Integer, primary_key=True)
    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)
    #: Name / Title for this Application
    name = Column(Unicode(length=255), unique=True)
    #: slug used in urls etc
    short_name = Column(Unicode(length=255), unique=True)
    #: description
    description = Column(Unicode(length=255))
    #: long description
    long_description = Column(UnicodeText)
    #: Allow anonymous contributors to participate in the application tasks
    allow_anonymous_contributors = Column(Boolean, default=True)
    ## TODO: What is this?
    long_tasks = Column(Integer, default=0)
    #: Boolean integer (0,1) indicating that \
    #: this App should be hidden from everyone but Administrators
    hidden = Column(Integer, default=0)
    #: owner (id)
    owner_id = Column(Integer, ForeignKey('user.id'))
    ## Following may not be relevant ...
    ## TODO: ask about these
    #: estimate of time it should take for user
    time_estimate = Column(Integer, default=0)
    #: time limit for a task
    time_limit = Column(Integer, default=0)
    calibration_frac = Column(Float, default=0)
    bolt_course_id = Column(Integer, default=0)
    #: category(id)
    category_id = Column(Integer, ForeignKey('category.id'))
    #: Standard JSON blob for additional data. This field also
    #: stores information used by PyBossa, such as the app thumbnail,
    #: the schedule mode, and the task presenter.
    #:
    #:    {
    #:       task_presenter: [html/javascript],
    #:       thumbnail: [url to the thumbnail image]
    #:       sched: [scheduling mode]
    #:    }
    #:
    info = Column(JSONType, default=dict)

    ## Relationships
    #: `Task`s for this app.`
    tasks = relationship('Task', cascade='all, delete-orphan', backref='app')
    #: `TaskRun`s for this app.`
    task_runs = relationship('TaskRun', backref='app',
                             cascade='all, delete-orphan',
                             order_by='TaskRun.finish_time.desc()')
    #: `Featured` or not for this app
    featured = relationship('Featured', cascade='all, delete-orphan')
    #: `category` or not for this app
    category = relationship('Category', cascade='all')

    #: Percentage of completed tasks based on Task.state
    #: (0 not done, 1 completed)
    def completion_status(self):
        """Returns the percentage of submitted Tasks Runs done"""
        sql = text('''SELECT COUNT(task_id) FROM task_run WHERE app_id=:app_id''')
        results = db.engine.execute(sql, app_id=self.id)
        for row in results:
            n_task_runs = float(row[0])
        sql = text('''SELECT SUM(n_answers) FROM task WHERE app_id=:app_id''')
        results = db.engine.execute(sql, app_id=self.id)
        for row in results:
            if row[0] is None:
                n_expected_task_runs = float(30 * n_task_runs)
            else:
                n_expected_task_runs = float(row[0])
        pct = float(0)
        if n_expected_task_runs != 0:
            pct = n_task_runs / n_expected_task_runs
        return pct

    def n_completed_tasks(self):
        """Returns the number of Tasks that are completed"""
        completed = 0
        for t in self.tasks:
            if t.state == "completed":
                completed += 1
        return completed

    def last_activity(self):
        sql = text('''SELECT finish_time FROM task_run WHERE app_id=:app_id
                   ORDER BY finish_time DESC LIMIT 1''')
        results = db.engine.execute(sql, app_id=self.id)
        for row in results:
            if row is not None:
                return pretty_date(row[0])
            else:
                return None


class Featured(db.Model, DomainObject):
    '''A Table with Featured Apps.
    '''
    __tablename__ = 'featured'
    #: Unique id for this app (autogenerated)
    id = Column(Integer, primary_key=True)
    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)
    #: Name / Title for this Application
    app_id = Column(Integer, ForeignKey('app.id'))


class Category(db.Model, DomainObject):
    '''A Table with Categories for Applications.'''
    __tablename__ = 'category'
    #: Unique id for this app (autogenerated)
    id = Column(Integer, primary_key=True)
    #: Name / Title for this Application
    name = Column(Text, nullable=False, unique=True)
    #: slug / Category slug
    short_name = Column(Text, nullable=False, unique=True)
    #: description / Description for the category
    description = Column(Text, nullable=False)
    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)


class Task(db.Model, DomainObject):
    '''An individual Task which can be performed by a user. A Task is
    associated to an App.
    '''
    __tablename__ = 'task'
    #: unique id (automatically generated)
    id = Column(Integer, primary_key=True)
    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)
    #: ForeignKey to App.id (NB: use task relationship rather than this field
    #: in normal use
    app_id = Column(Integer, ForeignKey('app.id'))
    #: a StateEnum instance
    # TODO: state should be an integer?
    state = Column(UnicodeText, default=u'ongoing')
    #: Quorum (number of times this task should be done by different users)
    quorum = Column(Integer, default=0)
    #: Boolean indicating whether this is a calibration Task or not.
    calibration = Column(Integer, default=0)
    #: Value between 0 and 1 indicating priority of task within App
    #: (higher = more important)
    priority_0 = Column(Float, default=0)
    #: all configuration / details of the Task is stored in info which is
    #: an arbitrary JSON object. (Usually expected to be a hash/dict)
    #: For example for an image classification project this would be::
    #:
    #:    {
    #:       url: [image-url],
    #:       question: [is this a person]
    #:    }
    info = Column(JSONType, default=dict)
    #: Number of answers or TaskRuns per task
    n_answers = Column(Integer, default=30)

    ## Relationships
    #: `TaskRun`s for this task`
    task_runs = relationship('TaskRun', cascade='all, delete-orphan', backref='task')

    def pct_status(self):
        """Returns the percentage of Tasks that are completed"""
        # DEPRECATED: self.info.n_answers will be removed
        # DEPRECATED: use self.t.n_answers instead
        if (self.info.get('n_answers')):
            self.n_answers = int(self.info['n_answers'])
        if self.n_answers != 0 and self.n_answers != None:
            return float(len(self.task_runs)) / self.n_answers
        else:
            return float(0)


class TaskRun(db.Model, DomainObject):
    '''A run of a given task by a specific user.
    '''
    __tablename__ = 'task_run'
    #: id
    id = Column(Integer, primary_key=True)
    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)
    #: application id of this task run
    app_id = Column(Integer, ForeignKey('app.id'))
    #: task id of this task run
    task_id = Column(Integer, ForeignKey('task.id'))
    #: user id of performer of this task
    user_id = Column(Integer, ForeignKey('user.id'))
    # ip address of this user (only if anonymous)
    user_ip = Column(Text)
    #: finish time (iso8601 formatted string)
    finish_time = Column(Text, default=make_timestamp)

    #: timeout for task
    timeout = Column(Integer)
    #: See same attribute in Task
    calibration = Column(Integer)
    info = Column(JSONType, default=dict)
    '''General writable field that should be used by clients to record results\
    of a TaskRun. Usually a template for this will be provided by Task
    For example::
        result: {
            whatever information shoudl be recorded -- up to task presenter
        }
    '''


class User(db.Model, DomainObject, flaskext.login.UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)
    #: email address ...
    email_addr = Column(Unicode(length=254), unique=True)
    #: user name
    name = Column(Unicode(length=254), unique=True)
    #: full name
    fullname = Column(Unicode(length=500))
    #: locale
    locale = Column(Unicode(length=254))
    #: api key
    api_key = Column(String(length=36), default=make_uuid, unique=True)
    passwd_hash = Column(Unicode(length=254), unique=True)
    #: Adming flag Boolean Integer (0,1)
    admin = Column(Boolean, default=False)
    #: TODO: find out ... bossa specific
    category = Column(Integer)
    #: TODO: find out ...
    flags = Column(Integer)
    # Twitter user_id field
    twitter_user_id = Column(BigInteger, unique=True)
    # Facebook user_id field
    facebook_user_id = Column(BigInteger, unique=True)
    # Google user_id field
    google_user_id = Column(String, unique=True)
    # CKAN API key field
    ckan_api = Column(String, unique=True)
    #: arbitrary additional information about the user in a JSON dict.
    info = Column(JSONType, default=dict)

    def get_id(self):
        '''id for login system. equates to name'''
        return self.name

    def set_password(self, password):
        self.passwd_hash = generate_password_hash(password)

    def check_password(self, password):
        # OAuth users do not have a password
        if self.passwd_hash:
            return check_password_hash(self.passwd_hash, password)
        else:
            return False

    @classmethod
    def by_name(cls, name):
        '''Lookup user by (user)name.'''
        return db.session.query(User).filter_by(name=name).first()

    ## Relationships
    #: `Task`s for this user
    task_runs = relationship('TaskRun', backref='user')
    apps = relationship('App', backref='owner')

class Team(db.Model, DomainObject):
    __tablename__ = 'team'
    id = Column(Integer, primary_key=True)
    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)
    #: team name
    name = Column(Unicode(length=50), unique=True)
    #: description
    description = Column(Unicode(length=200))
    #: owner
    owner_id = Column(Integer, ForeignKey('user.id'))
    #: Public flag Boolean Integer (0,1)
    public = Column(Boolean, default=False)

    #: TODO: find out ...
    #flags = Column(Integer)
    #: arbitrary additional information about the user in a JSON dict.
    #info = Column(JSONType, default=dict)
    def get_id(self):
        '''id for login system. equates to name'''
        return self.name

    @classmethod
    def by_name(cls, name):
        '''Lookup user by (user)name.'''
        return db.session.query(Team).filter_by(name=name).first()

    user2team = relationship('User2Team', cascade='all, delete-orphan')
    user = relationship('User')

class User2Team(db.Model, DomainObject):
    __tablename__ = 'user2team'
    #: id
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    team_id = Column(Integer, ForeignKey('team.id', ondelete='CASCADE'), primary_key=True)     

    #: created timestamp (automatically set)
    created = Column(Text, default=make_timestamp)

    def get_id(self):
        '''id for login system. equates to name'''
        return self.name

    team = relationship('Team')
    user = relationship('User')

@event.listens_for(User, 'before_insert')
def make_admin(mapper, conn, target):
    users = conn.scalar('select count(*) from "user"')
    if users == 0:
        target.admin = True
        #print "User %s is the first one, so we make it an admin" % target.name
