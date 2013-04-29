#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    try:
        from local_env import DJANGO_SETTINGS_MODULE
    except ImportError:
        DJANGO_SETTINGS_MODULE = "sadiki.production"

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
