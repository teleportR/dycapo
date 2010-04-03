"""
This file is part of Dycapo.
    Copyright (C) 2009, 2010 FBK Foundation, (http://www.fbk.eu)
    Authors: SoNet Group (see AUTHORS)
    Dycapo is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Dycapo is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with Dycapo.  If not, see <http://www.gnu.org/licenses/>.

"""
"""
Handles HTTP BASIC authorization on Dycapo. 
Credits: http://www.davidfischer.name/2009/10/django-authentication-and-mod_wsgi/
See docs/http.conf on how to use it
"""
import os
import sys
sys.stdout = sys.stderr
sys.path.append('/home/bodom_lx/Projects/')
sys.path.append('/home/bodom_lx/Projects/dycapo')

os.environ['DJANGO_SETTINGS_MODULE'] = 'dycapo.settings'

from django.contrib.auth.models import User
from django import db

def check_password(environ, user, password):
    """
    Authenticates apache/mod_wsgi against Django's auth database.
    """

    db.reset_queries() 

    kwargs = {'username': user, 'is_active': True} 

    try:
        # checks that the username is valid
        try:
            user = User.objects.get(**kwargs)
        except User.DoesNotExist:
            return None

        # verifies that the password is valid for the user
        if user.check_password(password):
            return True
        else:
            return False
    finally:
        db.connection.close()