#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Feed Controller

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, logging

log = logging.getLogger()

from models import Feed, Group, Item, Filter, Favicon
from config import settings
from decorators import cached_method
import feedparser

class FeedController:

    def __init__(self):
        pass

    def get_feeds(self):
        """Return all feeds"""
        return Feed.select()
        
    def add_feed(self, url, site_url = None, title = None, group = None):
        """Add a feed to the database"""
        # existing feed?
        try:
            f = Feed.get(Feed.url == url)
        except Feed.DoesNotExist:
            f = Feed.create(url = url, title=title, site_url=site_url)
        return f
    
    def fetch_feed(self, feed):
        print feed.url
        

def feed_worker(feed):
    fc = FeedController()
    fc.fetch(feed)