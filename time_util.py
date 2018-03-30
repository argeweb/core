#!/usr/bin/env python
# -*- coding: utf-8 -*-
from argeweb.core import settings
from datetime import datetime, timedelta
import pytz


def utc_tz():
    return pytz.timezone('UTC')


def local_tz():
    # TODO 時區個人化
    s = pytz.timezone(settings.get('timezone')['local'])
    return s


def localize(dt, tz=None):
    if not dt.tzinfo:
        dt = utc_tz().localize(dt)
    if not tz:
        tz = local_tz()
    return dt.astimezone(tz)


def last_month(year=None, month=None):
    # 回傳指定月份的上一個月
    n = datetime.now()
    if year:
        n = n.replace(year=year)
    if month:
        n = n.replace(month=month)
    n = n.replace(day=1) - timedelta(days=1)
    return n.replace(hour=23, minute=59, second=59, microsecond=9999)


def next_month(year=None, month=None):
    # 回傳指定月份的下一個月
    n = datetime.now()
    if year:
        n = n.replace(year=year)
    if month:
        n = n.replace(month=month)
    n = n.replace(day=28) + timedelta(days=4)
    n = n.replace(day=1)
    return n.replace(hour=0, minute=0, second=0, microsecond=0)


def day_range_in_month(year=None, month=None):
    # 回傳指定月份的範圍
    n = datetime.now()
    if year:
        n = n.replace(year=year)
    if month:
        n = n.replace(month=month)
    d_last = next_month(n.year, n.month) - timedelta(microseconds=1)
    d_last = d_last.replace(hour=23, minute=59, second=59, microsecond=9999)
    d_start = n.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return [d_start, d_last]


def count_minute(datetime_1, datetime_2=None):
    # 回傳 2個時間相距的分鐘數
    d1 = d2 = None
    if datetime_1 is None:
        return -1
    if isinstance(datetime_1, datetime):
        d1 = datetime_1
    if isinstance(datetime_1, basestring):
        d1 = datetime.strptime(datetime_1, '%Y/%m/%d %H:%M')
    if datetime_2 is None:
        d2 = datetime.now() + timedelta(hours=8)
    if isinstance(datetime_2, datetime):
        d2 = datetime_2
    if isinstance(datetime_2, basestring):
        d2 = datetime.strptime(datetime_2, '%Y/%m/%d %H:%M')
    if d1 is None or d2 is None:
        return None
    return (d1 - d2).total_seconds() / 60
