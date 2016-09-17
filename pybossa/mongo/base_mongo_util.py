from flask import current_app
import datetime

class BaseMongoUtil(object):
    def __init__(self, collection_name):
        self.collection_name = collection_name

    def insert_one(self, doc):
        doc['timestamp'] = datetime.datetime.now()
        current_app.mongo.db[self.collection_name].insert_one(doc)
