from subprocess import check_call, CalledProcessError

from flask import current_app
from hdfs.ext.kerberos import KerberosClient


class HDFSKerberos(KerberosClient):

    def __init__(self, url, user, keytab=None, proxy=None):
        self.url = url
        self.user = user
        self.keytab = keytab
        self.proxy = proxy
        super(HDFSKerberos, self).__init__(url, proxy=proxy)

    def should_reinit(self):
        try:
            check_call(['klist', '-s'])
            return False
        except CalledProcessError:
            return True

    def reinit(self):
        current_app.logger.info('running kinit')
        try:
            principal = self.proxy or self.user
            check_call(['kinit', '-kt', self.keytab, principal])
        except CalledProcessError as e:
            current_app.logger.exception(e.output)
            raise

    def get_ticket(self):
        if self.should_reinit():
            self.reinit()

    def put(self, path, content):
        self.get_ticket()
        self.write(path, content, overwrite=True)

    def get(self, path, **kwargs):
        self.get_ticket()
        with self.read(path, **kwargs) as reader:
            return reader.read()
