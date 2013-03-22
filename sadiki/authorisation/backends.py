# -*- coding: utf-8 -*-
from django.core.validators import email_re
from django.contrib.auth.backends import ModelBackend
#from django.forms.fields import email_re
from sadiki.core.utils import get_user_by_email

class EmailAuthBackend(ModelBackend):

    def authenticate(self, username=None, password=None):
        #If username is an email address, then try to pull it up
        if email_re.search(username):
            user = get_user_by_email(username)
            if user:
                if user.check_password(password):
                    return user
            else:
                return None
