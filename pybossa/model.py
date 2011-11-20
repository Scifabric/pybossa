import os 
from glob import iglob
import logging
import datetime
import time

from sqlalchemy import create_engine
from sqlalchemy import Integer, Unicode, Float, UnicodeText
from sqlalchemy.schema import Table, MetaData, Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
import flaskext.login

log = logging.getLogger(__name__)

Session = scoped_session(sessionmaker())

def set_engine(engine):
    Session.configure(bind=engine)
    Base.metadata.bind = engine

def make_timestamp_as_int():
    now = datetime.datetime.now()
    return time.mktime(now.timetuple())


class DomainObject(object):
    def dictize(self):
        out = {}
        for col in self.__table__.c:
            out[col.name] = getattr(self, col.name)
        return out

    @classmethod
    def undictize(cls, dict_):
        raise NotImplementedError()
    

Base = declarative_base(cls=DomainObject)


class App(Base):
    __tablename__ = 'bossa_app'
    id                  = Column(Integer, primary_key=True)
    create_time         = Column(Integer, default=make_timestamp_as_int)
    name                = Column(Unicode(length=255), unique=True)
    short_name          = Column(Unicode(length=255), unique=True)
    description         = Column(Unicode(length=255))
    long_jobs           = Column(Integer)
    hidden              = Column(Integer)
    bolt_course_id      = Column(Integer)
    time_estimate       = Column(Integer)
    time_limit          = Column(Integer)
    calibration_frac    = Column(Float)
    info                = Column(UnicodeText)

class Task(Base):
    __tablename__ = 'bossa_job'
    id                  = Column(Integer, primary_key=True)
    create_time         = Column(Integer, default=make_timestamp_as_int)
    app_id              = Column(Integer, ForeignKey('bossa_app.id'))
    batch_id            = Column(Integer, ForeignKey('bossa_batch.id'))
    state               = Column(Integer)
    info                = Column(UnicodeText)
    calibration         = Column(Integer)
    priority_0          = Column(Float)

class TaskRun(Base):
    __tablename__ = 'bossa_job_inst'
    id                  = Column(Integer, primary_key=True)
    create_time         = Column(Integer, default=make_timestamp_as_int)
    app_id              = Column(Integer, ForeignKey('bossa_app.id'))
    job_id              = Column(Integer, ForeignKey('bossa_job.id'))
    user_id             = Column(Integer, ForeignKey('user.id'))
    batch_id            = Column(Integer, ForeignKey('bossa_batch.id'))
    finish_time         = Column(Integer)
    timeout             = Column(Integer)
    calibration         = Column(Integer)
    info                = Column(UnicodeText)

class User(Base, flaskext.login.UserMixin):
    __tablename__ = 'user'
    id             = Column(Integer, primary_key=True)
    create_time         = Column(Integer, default=make_timestamp_as_int)
    email_addr          = Column(Unicode(length=254), unique=True)
    name                = Column(Unicode(length=254), unique=True)
    passwd_hash         = Column(Unicode(length=254), unique=True)
    # bossa specific
    category            = Column(Integer)
    flags               = Column(Integer)
    info                = Column(UnicodeText)

    def get_id(self):
        '''id for login system. equates to name'''
        return self.name

    @classmethod
    def by_name(cls, name):
        '''Lookup user by (user)name.'''
        return Session.query(User).filter_by(name=name).first()

class Batch(Base):
    __tablename__ = 'bossa_batch'
    id                  = Column(Integer, primary_key=True)
    create_time         = Column(Integer, default=make_timestamp_as_int)
    name                = Column(Unicode(length=255))
    app_id              = Column(Integer, ForeignKey('bossa_app.id'))
    calibration         = Column(Integer)

