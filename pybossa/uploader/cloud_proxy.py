from flask import Response, current_app
from pybossa.uploader.cloud_store import CloudStoreUploader


MAX_AGE = 365 * 24 * 60 * 60


class CloudProxyUploader(CloudStoreUploader):

    def send_file(self, filename):
        try:
            key = self.bucket.get_key(filename, validate=False)
            content = key.get_contents_as_string()
            response = Response(content, content_type=key.content_type)
            response.cache_control.max_age = MAX_AGE
            response.cache_control.public = True
        except Exception as e:
            current_app.logger.exception(e)
            return Response('Not Found', 404)
        return response
