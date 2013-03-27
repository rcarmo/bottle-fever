#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Feed Controller

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, logging
import re, time, datetime
import socket, hashlib, urllib, urllib2, urlparse

log = logging.getLogger()

from models import Feed, User, Group, Item, Filter, Link, Reference, Favicon, db
from peewee import fn, JOIN_LEFT_OUTER
from config import settings
from decorators import cached_method
from utils.timekit import http_time
from utils.urlkit import expand
from utils import tb
from bs4 import BeautifulSoup
import markup.feedparser as feedparser

feedparser.USER_AGENT = settings.fetcher.user_agent

def get_entry_content(entry):
    """Select the best content from an entry"""

    candidates = entry.get('content', [])
    if 'summary_detail' in entry:
        candidates.append(entry.summary_detail)
    for c in candidates:
        if 'html' in c.type: 
            return c.value
    if candidates:
        return candidates[0].value
    return ''
    
    
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
    """Select the best timestamp for an entry"""
    for header in ['modified', 'issued', 'created']:
        when = entry.get(header+'_parsed',None)
        if when:
            return time.mktime(when)
    return time.time()
    
    
def get_feed_updated(feed):
    """Get the date a feed was last updated"""
    for header in ['updated', 'published']:
        when = entry.get(header+'_parsed',None)
        if when:
            return time.mktime(when)
    return time.time()


def get_link_references(content):
    """Grab all the links from a post"""
    soup = BeautifulSoup(content, settings.fetcher.parser)
    links = soup.find_all('a', href=re.compile('.+'))
    return [l['href'] for l in links]


def expand_links(feed, links):
    """Try to expand a link without locking the database"""
    result = {}
    for l in links:
        (schema, netloc, path, params, query, fragment) = urlparse.urlparse(l)
        if netloc and schema in ['http','https']:
            try:
                link = Link.get(url = l)
                result[l] = link.expanded_url
                db.close()
            except Link.DoesNotExist:
                expanded_url = expand(l)
                Link.create(url = l, expanded_url = expanded_url, when = time.time())
                db.close()
                result[l] = expanded_url
        else:
            result[l] = l
    return result
    

class FeedController:


    def get_items_from_feed(self, id):
        """Return all items from a given feed"""

        result = [i.fields() for i in Item.select().where(Item.feed == id)]
        db.close()
        return result


    def get_feeds_with_counts(self, enabled = True):
        """Return feeds - defaults to returning enabled feeds only"""
        
        def _merge(i):
            r = i.fields()
            r.update({'item_count': i.item_count})
            return r
        
        result = [i for i in Feed.select().annotate(Item,fn.Count(Item.id).alias('item_count')).where(Feed.enabled == enabled)]
        db.close()
        result = map(_merge, result)
        return result

        
    def get_feeds(self, all = False):
        """Return feeds - defaults to returning enabled feeds only"""
        if all:
            result = [f for f in Feed.select()]
        else:
            result = [f for f in Feed.select(Feed.enabled == True)]
        db.close()
        return result
        
        
    def add_feed(self, url, site_url = None, title = None, group = None):
        """Add a feed to the database"""
        # existing feed?
        try:
            f = Feed.get(Feed.url == url)
        except Feed.DoesNotExist:
            f = Feed.create(url = url, title=title, site_url=site_url)
        db.close()
        return f
    
    
    def fetch_feed(self, feed):
        socket.setdefaulttimeout(settings.fetcher.timeout) 

        if not feed.enabled:
            return

        (schema, netloc, path, params, query, fragment) = urlparse.urlparse(feed.url)

        now = time.time()
        
        if feed.last_checked:
            if feed.ttl:
                if (now - feed.last_checked) < (feed.ttl * 60):
                    log.info("%s - throttled (TTL)" % netloc)
                    return
                
            if (now - feed.last_checked) < settings.fetcher.min_interval:
                log.info("%s - throttled (interval)" % netloc)
                return
    
        if feed.last_modified:
            if (now - feed.last_modified) < settings.fetcher.min_interval:
                log.info("%s - throttled (last-modified)" % netloc)
                return
            modified = http_time(feed.last_modified)
        else:
            modified = None
        
        try:
            res = feedparser.parse(feed.url, etag = feed.etag, modified = modified)
        except Exception, e:
            log.error("Could not fetch %s: %s" % (feed.url, e))
            socket.setdefaulttimeout(None) 
            feed.last_checked = now
            feed.save()
            db.close()
            return
            
        feed.last_checked = now
        socket.setdefaulttimeout(None) 

        
        status    = res.get('status', 503)
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
                log.warn("%s: %s" % (netloc, message))
            if leave: 
                feed.last_status = 599 # Network connect timeout error (Unknown)
                feed.error_count = feed.error_count + 1
                if feed.error_count > settings.fetcher.error_threshold:
                    feed.enabled = False
                    log.warn("%s - disabling %s" % (netloc, feed.url))
                feed.save()
                db.close()
                return
        
        if status == 304: # not modified
            log.info("%s - not modified." % netloc)
            feed.last_status = status
            feed.save()
            db.close()
            return
        elif status == 410: # gone
            log.info("%s - gone, disabling %s" % (netloc, feed.url))
            feed.enabled = False
            feed.last_status = status
            feed.save()
            db.close()
            return
        elif status not in [200,301,302,307,308]:
            log.warn("%s - %d, aborting" % (netloc,status))
            feed.last_status = status
            feed.error_count = feed.error_count + 1
            if feed.error_count > settings.fetcher.error_threshold:
                feed.enabled = False
                log.warn("%s - disabling %s" % (netloc, feed.url))
            feed.save()
            db.close()
            return
        
        if 'content-type' in headers and 'xml' not in headers['content-type']:
            log.warn("%s - content-type %s, proceeding" % (netloc, headers['content-type']))
        
        ttl = res.feed.get('ttl',None)
        etag = res.feed.get('etag',None)
        last_modified = res.feed.get('modified_parsed',None)
        
        if status in [301,308]:
            feed.url = res.href
        feed.ttl = ttl
        feed.etag = etag
        feed.last_modified = time.mktime(last_modified) if last_modified else None
        feed.last_status = status
        feed.error_count = 0
        feed.save()
        db.close()

        res.entries.reverse()
        
        entries = []
        
        now = time.time()
        for entry in res.entries:
            when = get_entry_timestamp(entry)
            # skip ancient feed items
            if (now - when) < settings.fetcher.max_history:
                continue

            guid = get_entry_id(entry)
            try:
                item = Item.get(guid = guid)
                # if item is already in database with same timestamp, then skip it
                # TODO: handle item content updates - potentially very expensive, we'll see later on
                if when == item.when:
                    db.close()
                    continue
            except Item.DoesNotExist:
                db.close()
                pass

            content = get_entry_content(entry)
            if len(content):
                hrefs = get_link_references(content)
            else:
                hrefs = []
            hrefs.append(entry.link)

            now = time.time()
            hrefs = expand_links(feed, set(hrefs))
            log.debug("%s - %d links in %fs" % (netloc, len(hrefs),time.time()-now))
            url = hrefs[entry.link]
            hrefs = list(set(hrefs.values()))

            # stack these for commiting to the database later on
            entries.append({'guid'   : guid,
                            'feed'   : feed,
                            'title'  : get_entry_title(entry),
                            'author' : get_entry_author(entry,res.feed),
                            'html'   : content,
                            'url'    : url,
                            'tags'   : get_entry_tags(entry),
                            'when'   : when,
                            'hrefs'  : hrefs})
        
        log.debug("%s - %d entries in %fs" % (netloc, len(entries),time.time()-now))
        now = time.time()
        
        records = 0
        db.connect()
        for entry in entries:
            try:
                item = Item.get(guid = entry['guid'])
            except Item.DoesNotExist:
                item = Item.create(**entry)
            records += 1
                
            for url in entry['hrefs']:
                try:
                    link = Link.get(url = url)
                except Link.DoesNotExist:
                    try:
                        link = Link.get(expanded_url = url)
                    except Link.DoesNotExist:
                        expanded_url = expand(url)
                        link = Link.create(url = url, expanded_url = expanded_url, when=time.time())
                        records += 1
                try:
                    reference = Reference.get(item = item, link = link)
                except Reference.DoesNotExist:
                    reference = Reference.create(item = item, link = link)
                    records += 1

        db.close()
        log.debug("%s - %d records in %fs" % (netloc, records,time.time()-now))

        # TODO: favicons, download linked content, extract keywords, the works.
        

def feed_worker(feed):
    # Use a private controller for multiprocessing
    fc = FeedController()
    fc.fetch_feed(feed)
