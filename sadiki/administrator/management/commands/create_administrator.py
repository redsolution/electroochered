# -*- coding: utf-8 -*-
"""
Создаем администратора из командной строки
"""
from django.contrib.auth.models import User, Permission, Group
from django.core.management.base import BaseCommand
from optparse import make_option
from sadiki.core.permissions import ADMINISTRATOR_PERMISSION, \
    ADMINISTRATOR_GROUP_NAME
import getpass
import os
import re
import sys

RE_VALID_USERNAME = re.compile('[\w\..@+-]+$')


def create_administrator(username, password, first_name=u'', last_name=u''):
    """Create administrator"""
    administrator_group = Group.objects.get(name=ADMINISTRATOR_GROUP_NAME)
    user = User.objects.create_user(username, u'', password)
    user.first_name = first_name
    user.last_name = last_name
    user.is_staff = True
    user.save()
    user.groups.add(administrator_group)

    return user


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default=None,
            help='Specifies the username for the superuser.'),
        )
    help = 'Used to create a administrator.'

    def handle(self, *args, **options):
        username = options.get('username', None)

        # Try to determine the current system user's username to use as a default.
        try:
            import pwd
            default_username = pwd.getpwuid(os.getuid())[0].replace(' ', '').lower()
        except (ImportError, KeyError):
            # KeyError will be raised by getpwuid() if there is no
            # corresponding entry in the /etc/passwd file (a very restricted
            # chroot environment, for example).
            default_username = ''

        # Determine whether the default username is taken, so we don't display
        # it as an option.
        if default_username:
            try:
                User.objects.get(username=default_username)
            except User.DoesNotExist:
                pass
            else:
                default_username = ''

        # Prompt for username/email/password. Enclose this whole thing in a
        # try/except to trap for a keyboard interrupt and exit gracefully.
        try:

            # Get a username
            while 1:
                if not username:
                    input_msg = 'Username'
                    if default_username:
                        input_msg += ' (Leave blank to use %r)' % default_username
                    username = raw_input(input_msg + ': ')
                if default_username and username == '':
                    username = default_username
                if not RE_VALID_USERNAME.match(username):
                    sys.stderr.write("Error: That username is invalid. Use only letters, digits and underscores.\n")
                    username = None
                    continue
                try:
                    User.objects.get(username=username)
                except User.DoesNotExist:
                    break
                else:
                    sys.stderr.write("Error: That username is already taken.\n")
                    username = None

            # Get an first name
            first_name = raw_input('First name: ')

            # Get an first name
            last_name = raw_input('Last name: ')

            # Get a password
            while 1:
                password = getpass.getpass()
                password2 = getpass.getpass('Password (again): ')
                if password != password2:
                    sys.stderr.write("Error: Your passwords didn't match.\n")
                    password = None
                    continue
                if password.strip() == '':
                    sys.stderr.write("Error: Blank passwords aren't allowed.\n")
                    password = None
                    continue
                break

        except KeyboardInterrupt:
            sys.stderr.write("\nOperation cancelled.\n")
            sys.exit(1)

        create_administrator(username, password, first_name, last_name)
        print "Administrator created successfully."
