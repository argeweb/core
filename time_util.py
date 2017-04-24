#!/usr/bin/env python
# -*- coding: utf-8 -*-
from argeweb.core import settings
import pytz

def utc_tz():
    return pytz.timezone('UTC')


def local_tz():
    s = pytz.timezone(settings.get('timezone')['local'])
    return s


def localize(dt, tz=None):
    if not dt.tzinfo:
        dt = utc_tz().localize(dt)
    if not tz:
        tz = local_tz()
    return dt.astimezone(tz)
