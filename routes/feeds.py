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
from config import settings

fc = FeedController(settings)


@route('/feed/<id:int>')
@view('feeds/items')
def item_list(id):
    """Render all items from a given feed"""
    try:
        items = fc.get_items_from_feed(id)
        log.debug(items[0])
    except:
        log.error(tb())
        abort(500,"Error accessing items for feed")

    return{'items':items, 'title': id}


@route('/feeds')
@view('feeds/index')
def index():
    """Render a feed index"""
    try:
        feeds = fc.get_feeds_with_counts()
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
        {'label': 'Status',     'field': 'last_status'},
        {'label': 'Items',      'field': 'item_count'},
    ]
    return {'headers': headers, 'feeds': feeds, 'title': 'feeds'}

