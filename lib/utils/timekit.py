#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2012, Rui Carmo
Description: Utility functions for handling date and time information
License: MIT (see LICENSE.md for details)
"""

import os, sys, time, math, re, logging
from markup.feedparser import _parse_date
import gettext
gettext.textdomain('date')
_ = gettext.gettext

log = logging.getLogger()


# Embrace and extend Mark's feedparser mechanism

_textmate_date_re = \
    re.compile('(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$')


def parse_date(date):
    """Parse a TextMate date (YYYY-MM-DD HH:MM:SS, no time zone, assume it's always localtime)"""

    m = _textmate_date_re.match(date)
    if not m:
        return time.mktime(_parse_date(date))
    return time.mktime(time.localtime(calendar.timegm(time.gmtime(time.mktime(time.strptime(date,
                       '%Y-%m-%d %H:%M:%S'))))))


def iso_time(value=None):
    """Format a timestamp in ISO format"""

    if value == None:
        value = time.localtime()
    tz = time.timezone / 3600
    return time.strftime('%Y-%m-%dT%H:%M:%S-', value) + '%(tz)02d:00' \
        % vars()


def http_time(value=None):
    """Format a timestamp for HTTP headers"""

    if value == None:
        value = time.time()
    return time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                         time.gmtime(value))


def plain_date(date, rss=False):
    """Format a date consistently"""

    if isinstance(date, float) or isinstance(date, int):
        date = time.localtime(date)

    # trickery to replace leading zero in month day

    mday = time.strftime(' %d', date).replace(' 0', ' ').strip()
    weekday = _(time.strftime('%A', date))
    month = _(time.strftime('%b', date))
    year = time.strftime('%Y', date)

    # build English ordinal suffixes

    day = int(mday)
    if day > 20:
        day = int(mday[1])
    try:
        suffix = ['th', 'st', 'nd', 'rd'][day]
    except:
        suffix = 'th'
    if rss:
        return _('rss_update_date_format') % locals()
    else:
        return _('journal_date_format') % locals()


def fuzzy_time(date=None):
    intervals = {
        '00:00-00:59': 'latenight',
        '01:00-03:59': 'weehours',
        '04:00-06:59': 'dawn',
        '07:00-08:59': 'breakfast',
        '09:00-12:29': 'morning',
        '12:30-14:29': 'lunchtime',
        '14:30-16:59': 'afternoon',
        '17:00-17:29': 'teatime',
        '17:30-18:59': 'lateafternoon',
        '19:00-20:29': 'evening',
        '20:30-21:29': 'dinnertime',
        '21:30-22:29': 'night',
        '22:30-23:59': 'latenight',
    }
    if isinstance(date, float) or isinstance(date, int):
        date = time.localtime(date)
    then = time.strftime('%H:%M', date)
    for i in intervals.keys():
        (l, u) = i.split('-')
        # cheesy (but perfectly usable) string comparison
        if l <= then and then <= u:
            return _(intervals[i])
    return None


def relative_time(value=None, addtime=False):
    """
    A simple time string
    """

    value = float(value)
    if addtime:
        format = ', %H:%M'
    else:
        format = ''
    if time.localtime(value)[0] != time.localtime()[0]:

    # we have a different year

        format = ' %Y' + format
    format = time.strftime('%b', time.localtime(value)) + ' %d' \
        + format
    return time.strftime(format, time.localtime(value)).strip()


def time_since(older=None, newer=None, detail=2):
    """
    Human-readable time strings, based on Natalie Downe's code from
    http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    Assumes time parameters are in seconds
    """

    intervals = {  # corrected from the initial 31536000
        31556926: 'year',
        2592000: 'month',
        604800: 'week',
        86400: 'day',
        3600: 'hour',
        60: 'minute',
    }
    chunks = intervals.keys()

    # Reverse sort using a lambda for Python 2.3 compatibility
    chunks.sort(lambda x, y: y - x)

    if newer == None:
        newer = time.time()

    interval = newer - older
    if interval < 0:
        return _('some_time')

    # We should ideally do this:
    # raise ValueError('Time interval cannot be negative')
    # but it makes sense to fail gracefully here

    if interval < 60:
        return _('less_1min')

    output = ''
    for steps in range(detail):
        for seconds in chunks:
            count = math.floor(interval / seconds)
            unit = intervals[seconds]
            if count != 0:
                break
        if count > 1:
            unit = unit + 's'
        if count != 0:
            output = output + '%d %s, ' % (count, _(unit))
        interval = interval - count * seconds
    output = output[:-2]
    return output