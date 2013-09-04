#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Worker tasks

Created by: Rui Carmo
"""

from __future__ import absolute_import

import os, sys, re, logging, time, subprocess, json, itertools
from Queue import Queue, Empty

sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../lib'))

from config import settings
from utils.jobs import task
from utils.urlkit import fetch
from utils import Struct
from controllers import IndexController, FeedController as Controller

log = logging.getLogger()

items = []


def chunks(n, iterable):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


@task
def control_worker():
    """Update all feeds that are deemed suitable for fetching"""
    
    c = Controller(settings)

    now   = time.time()
    count = 0
    for f in c.get_feeds():
        if f.enabled:
            if (not f.last_checked) or (f.ttl and ((f.last_checked + f.ttl) > now) and ((f.last_checked + settings.fetcher.min_interval) > now)):
                fetch_worker.delay(f.id)
                #favicon_worker.delay(f.id)
                count += 1
    log.warn("Queued %d tasks" % count)
    index_worker.delay()
    return count


@task(max_retries=3)
def fetch_worker(feed_id):
    """Fetch a feed and check if it needs further processing"""

    c = Controller(settings)
    changed = c.fetch_feed(feed_id)
    if changed:
        parse_worker.delay(feed_id)
    

@task(max_retries=3)
def parse_worker(feed_id):
    """Parse a feed and queue up items for processing"""

    c = Controller(settings)
    for chunk in chunks(settings.fetcher.chunk_size, c.parse_feed(feed_id)):
        item_worker.delay(feed_id, chunk)


@task(max_retries=3)
def item_worker(feed_id, chunk):
    """Do whatever processing is required on an item prior to database insertion"""
    
    global items
    c = Controller(settings)
    for entry in chunk:
        guid = c.parse_item(entry)
        items.append(guid)


@task
def index_worker():
    global items
    for chunk in chunks(settings.fetcher.chunk_size, items):
        chunk_worker.delay(chunk)


@task(max_retries=3)
def chunk_worker(chunk):
    c = IndexController(settings)

    for guid in chunk:
        c.add_item(guid)


@task(max_retries=3)
def favicon_worker(feed_id):
    """Fetch the favicon for a given feed"""

    c = Controller(settings)
    c.update_favicon(feed_id)


@task(max_retries=3)
def imap_worker(item_id):
    """Deliver a feed item from our database to an IMAP folder"""
    
    c = Controller(settings)
