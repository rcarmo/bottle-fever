#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Static routes

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, logging
from bottle import abort, route, view, static_file

log = logging.getLogger()

from controllers.feeds import FeedController
from utils import tb

fc = FeedController()

@route('/feeds')
@view('feeds/index')
def index():
    """Render a feed index"""
    try:
        feeds = [f.fields() for f in fc.get_feeds()]
    except:
        log.error(tb())
        abort(500,"Error accessing feed data")
    headers = [
        {'label': 'Feed',       'field': 'title'},
        {'field': 'enabled',    'icon': 'icon-ok'},
        {'label': 'URL',        'field': 'url'},
        {'label': 'Site URL',   'field': 'site_url'},
        {'label': 'Modified',   'field': 'last_modified'},
        {'label': 'Checked',    'field': 'last_checked'},
    ]
    return {'headers': headers, 'feeds': feeds, 'title': 'feeds'}

@route('/<path:path>')
def send_static(path):
    """Static file handler"""
    return static_file(path, root='static')

