# CACHE
from pybossa.sentinel import Sentinel
sentinel = Sentinel()

# Signer
from pybossa.signer import Signer
signer = Signer()

# Mail
from flask.ext.mail import Mail
mail = Mail()

# Login Manager
from flask.ext.login import LoginManager
login_manager = LoginManager()

# Toolbar
from flask.ext.debugtoolbar import DebugToolbarExtension
toolbar = DebugToolbarExtension()

# Social Networks
from pybossa.util import Facebook
facebook = Facebook()

from pybossa.util import Twitter
twitter = Twitter()
