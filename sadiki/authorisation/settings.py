# -*- coding: utf-8 -*-
from django.conf import settings

VERIFICATION_KEY_DAYS = getattr(settings, 'VERIFICATION_KEY_DAYS', 3)
