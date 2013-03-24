#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Feed Controller

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, logging
import time, socket, hashlib, urllib2

log = logging.getLogger()

from models import Feed, Group, Item, Filter, Favicon, db
from config import settings
from decorators import cached_method
import feedparser

feedparser.USER_AGENT = settings.fetcher.user_agent
socket.setdefaulttimeout(settings.fetcher.timeout) 


def get_entry_content(entry):
    """Select the best content from an entry"""

    candidates = entry.get('content', [])
    if 'summary_detail' in entry:
        candidates.append(entry.summary_detail)
    for c in candidates:
        if 'html' in c.type: 
            return c.value
    if content:
        return content[0].value
    return None
    
    
def get_entry_title(entry):
    if 'title' in entry:
        return entry.title
    return "Untitled"
    

def get_entry_id(entry):
    """Get a useful id from a feed entry"""
    
    if 'id' in entry and entry.id: 
        if type(entry.id) is dict:
            return entry.id.values()[0]
        return entry.id

    content = get_entry_content(entry)
    if content: 
        return hashlib.sha1(content.encode('utf-8')).hexdigest()
    if 'link' in entry: 
        return entry.link
    if 'title' in entry: 
        return hashlib.sha1(entry.title.encode('utf-8')).hexdigest()


def get_entry_tags(entry):
    """Gather tags and return a comma-separated string"""
    
    tags = []
    for tag in entry.get('tags',[]):
        tags.append(tag['term'])
    return ','.join(set(tags))
    
    
def get_entry_author(entry, feed):
    """Divine authorship"""
    
    if 'name' in entry.get('author_detail',[]):
        return entry.author_detail.name
     
    elif 'name' in feed.get('author_detail', []):
        return feed.author_detail.name
    return None
    
    
def get_entry_timestamp(entry):
    for header in ['modified', 'issued', 'created']:
        when = entry.get(header+'_parsed',None)
        if when:
            return time.mktime(when)
    return time.time()


class FeedController:

    def get_feeds(self):
        """Return all feeds"""
        db.connect()
        result = [f for f in Feed.select()]
        db.close()
        return result
        
        
    def add_feed(self, url, site_url = None, title = None, group = None):
        """Add a feed to the database"""
        # existing feed?
        db.connect()
        try:
            f = Feed.get(Feed.url == url)
        except Feed.DoesNotExist:
            f = Feed.create(url = url, title=title, site_url=site_url)
        db.close()
        return f
    
    
    def fetch_feed(self, feed):
        try:
            res = feedparser.parse(feed.url, etag = feed.etag, modified = feed.last_modified)
        except Exception, e:
            log.error("Could not fetch %s: %s" % (feed.url, e))
            return
        
        status    = res.get('status', 200)
        headers   = res.get('headers', {})
        exception = res.get("bozo_exception", Exception()).__class__

        if exception != Exception:
            try:
                msg = "%s@%d" % (res.get("bozo_exception", "Unhandled"), res.bozo_exception.getMessage(),res.bozo_exception.getLineNumber())
            except:
                msg = ""
                pass
            # Map exceptions to warning messages
            message, leave = {
                socket.timeout                       : ("timed out", True),
                socket.error                         : (res.bozo_exception.args, True),
                socket.gaierror                      : (res.bozo_exception.args, True),
                IOError                              : (res.bozo_exception, True),
                feedparser.zlib.error                : ("broken compression", False),
                urllib2.URLError                     : (res.bozo_exception.args, True),
                AttributeError                       : (res.bozo_exception, True)
            }.get(exception,(msg,False))
            if message:
                log.warn("Feed %s: %s" % (feed.url, message))
            if leave: 
                return
        
        if status == 301:   # permanent redirect
            feed.url = res['url']
            feed.save()
        elif status == 304: # not modified
            return
        elif status == 410: # gone
            log.info("Feed %s is gone, marking as disabled" % feed.url)
            feed.enabled = False
            feed.save()
            return
        elif status not in [200,302,307]:
            log.warn("Feed %s gave result code %d, aborting" % (feed.url,status))
            return
        
        if 'content-type' in headers and 'xml' not in headers['content-type']:
            log.warn("Feed %s has strange content-type %s, proceeding" % (feed.url, headers['content-type']))
        
        res.entries.reverse()
        for entry in res.entries:
            guid = get_entry_id(entry)
            # TODO: handle updates
            db.connect()
            try:
                Item.get(guid = guid)
            except Item.DoesNotExist:
                Item.create(guid   = guid,
                            feed   = feed,
                            title  = get_entry_title(entry),
                            author = get_entry_author(entry,res.feed),
                            html   = get_entry_content(entry),
                            url    = entry.link,
                            tags   = get_entry_tags(entry),
                            when   = get_entry_timestamp(entry))
            db.close()


        

def feed_worker(feed):
    # Use a private controller for multiprocessing
    fc = FeedController()
    log.info("Worker processing %s" % feed.url)
    fc.fetch_feed(feed)