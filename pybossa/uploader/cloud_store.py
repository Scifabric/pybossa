from pybossa.uploader import Uploader
from flask import current_app as app
from flask import url_for
import traceback
from pybossa.cloud_store_api.connection import create_connection


class CloudStoreUploader(Uploader):

    def __init__(self):
        self._bucket = None

    @property
    def bucket(self):
        if not self._bucket:
            bucket = app.config['UPLOAD_BUCKET']
            conn_kwargs = app.config.get('S3_UPLOAD', {})
            conn = create_connection(**conn_kwargs)
            self._bucket = conn.get_bucket(bucket, validate=False)
        return self._bucket

    @staticmethod
    def key_name(container, filename):
        return '{}/{}'.format(container, filename)

    def _lookup_url(self, endpoint, values): # pragma: no cover
        """Override by the uploader handler."""
        try:
            # Create failover urls for avatars
            if '_avatar' in values['filename']:
                failover_url = url_for('static',
                                       filename='img/placeholder.user.png')
            else:
                failover_url = url_for('static',
                                       filename='img/placeholder.project.png')
            key = self.key_name(values['container'], values['filename'])
            key = self.bucket.get_key(key, validate=False)
            url = key.generate_url(0, query_auth=False).split('?')[0]
            return url
        except Exception:
            app.logger.exception('')
            return failover_url
        pass

    def _upload_file(self, file, container): # pragma: no cover
        """Override by the specific uploader handler."""
        try:
            key = self.key_name(container, file.filename)
            key = self.bucket.get_key(key, validate=False)
            key.set_contents_from_string(file.read(), policy='public-read')
            return True
        except Exception:
            app.logger.exception('Error uploading')
            return False

    def delete_file(self, name, container):  # pragma: no cover
        try:
            key = self.key_name(container, name)
            self.bucket.delete_key(key)
            return True
        except Exception:
            app.logger.warning('Error deleting upload')
            return False

    def file_exists(self, name, container):  #pragma: no cover
        """Override by the uploader handler."""
        key = self.key_name(container, name)
        return self.bucket.lookup(key)
