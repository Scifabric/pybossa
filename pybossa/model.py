import os 
from glob import iglob
import logging
import datetime
import time

from sqlalchemy import create_engine
from sqlalchemy import Integer, Unicode, Float, UnicodeText
from sqlalchemy.schema import Table, MetaData, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

log = logging.getLogger(__name__)


Base = declarative_base()
Session = scoped_session(sessionmaker())

def set_engine(engine):
    Session.configure(bind=engine)

def make_timestamp_as_int():
    now = datetime.datetime.now()
    return time.mktime(now.timetuple())

class App(Base):
    __tablename__ = 'bossa_app'
    id                  = Column(Integer, primary_key=True)
    # create_time         = Column(Integer, default=datetime.datetime.now())
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
    create_time         = Column(Integer)
    app_id              = Column(Integer)
    batch_id            = Column(Integer)
    state               = Column(Integer)
    info                = Column(UnicodeText)
    calibration         = Column(Integer)
    priority_0          = Column(Float)

class TaskRun(Base):
    __tablename__ = 'bossa_job_inst'
    id                  = Column(Integer, primary_key=True)
    create_time         = Column(Integer)
    app_id              = Column(Integer)
    job_id              = Column(Integer)
    user_id             = Column(Integer)
    batch_id            = Column(Integer)
    finish_time         = Column(Integer)
    timeout             = Column(Integer)
    calibration         = Column(Integer)
    info                = Column(UnicodeText)

class User(Base):
    __tablename__ = 'bossa_user'
    user_id             = Column(Integer, primary_key=True)
    category            = Column(Integer)
    flags               = Column(Integer)
    info                = Column(UnicodeText)

class Batch(Base):
    __tablename__ = 'bossa_batch'
    id                  = Column(Integer, primary_key=True)
    create_time         = Column(Integer)
    name                = Column(Unicode(length=255))
    app_id              = Column(Integer)
    calibration         = Column(Integer)

