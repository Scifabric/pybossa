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


from flaskext.login import current_user
import pybossa.model as model

def logged_in():
    return not current_user.is_anonymous()

def logged_user():
    user_id = current_user.get_id()
    return model.Session.query(model.User).filter(model.User.name==user_id).one()
