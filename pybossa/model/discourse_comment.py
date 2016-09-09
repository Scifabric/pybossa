from sqlalchemy import Integer
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSON

from pybossa.core import db
from pybossa.model import DomainObject



class DiscourseComment(db.Model, DomainObject):
    '''Task comment which hosted by discourse app.
    '''
    __tablename__ = 'discourse_comment'

    #: ID of the table
    #: Task.id of the task associated with this discourse comment topic.
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     primary_key=True,
                     nullable=False)

    #: Discourse topic id of this task
    discourse_topic_id = Column(Integer)