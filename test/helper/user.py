class User(object):
    """Class to help testing PyBossa"""
    def __init__(self, **kwargs):
        self.fullname = "John Doe"
        self.username = self.fullname.replace(" ", "").lower()
        self.password = "p4ssw0rd"
        self.email_addr = self.username + "@example.com"
