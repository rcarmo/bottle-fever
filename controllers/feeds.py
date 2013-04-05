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
from utils.urlkit import expand, fetch
from utils import tb
from bs4 import BeautifulSoup
import markup.feedparser as feedparser
try:
    import markup.speedparser.speedparser as speedparser
except ImportError, e: # speedparser or its dependencies are not available
    log.error("Error importing speedparser: %s" % e)
    pass


feedparser.USER_AGENT = settings.fetcher.user_agent

def get_entry_content(entry):
    """Select the best content from an entry"""

    candidates = entry.get('content', [])
    if 'summary_detail' in entry:
        candidates.append(entry.summary_detail)
    for c in candidates:
        if hasattr(c,'type'): # speedparser doesn't set this
            if 'html' in c.type: 
                return c.value
    if candidates:
        try:
            return candidates[0].value
        except AttributeError: # speedparser does this differently
            return candidates[0]['value']
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


    def after_fetch(self, feed, status = None, error = False):
        if status:
            feed.last_status = status
        if error:
            feed.error_count = feed.error_count + 1
        if feed.error_count > settings.fetcher.error_threshold:
            feed.enabled = False
            log.warn("%s - disabling %s" % (netloc, feed.url))
        feed.save()
        db.close()
    
    
    def fetch_feed(self, feed):

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
            response = fetch(feed.url, etag = feed.etag, last_modified = modified)
            log.debug("%s - %d, %d" % (feed.url, response['status'], len(response['data'])))
        except Exception, e:
            log.error("Could not fetch %s: %s" % (feed.url, e))
            # TODO: store reason properly
            # Network connect timeout error (Unknown)
            self.after_fetch(feed, status = 599, error = True)
            return
            
        feed.last_checked = now
        status = response['status']

        feed.last_status = status
        if status == 304: # not modified
            log.info("%s - not modified." % netloc)
            self.after_fetch(feed, status = status)
            return
        elif status == 410: # gone
            log.info("%s - gone, disabling %s" % (netloc, feed.url))
            feed.enabled = False
            self.after_fetch(feed, status = status)
            return
        elif status not in [200,301,302,307,308]:
            log.warn("%s - %d, aborting" % (netloc,status))
            self.after_fetch(feed, status = status, error = True)
            return

        if feed.error_count and feed.parsed_with == 1: # there were errors last time around, so let's try feedparser this time
            try:
                result = feedparser.parse(response['data'])
                feed.parsed_with = 2
            except Exception, e:
                log.error("Could not parse %s with feedparser: %s" % (feed.url, e))
                # Invalid response from upstream server
                self.after_fetch(feed, status = 502, error = True)
                return
        else:
            try:
                result = speedparser.parse(response['data'])
                feed.parsed_with = 1
            except Exception, e:
                log.error("Could not parse %s with speedparser: %s" % (feed.url, e))
                try:
                    result = feedparser.parse(response['data'])
                    feed.parsed_with = 2
                except Exception, e:
                    log.error("Could not parse %s with feedparser: %s" % (feed.url, e))
                    # Invalid response from upstream server
                    self.after_fetch(feed, status = 502, error = True)
                    return
        
        status    = response.get('status', 503)
        headers   = response.get('headers', {})
        exception = result.get("bozo_exception", Exception()).__class__

        if exception != Exception:
            try:
                msg = "%s@%d" % (result.get("bozo_exception", "Unhandled"), result.bozo_exception.getMessage(),result.bozo_exception.getLineNumber())
            except:
                msg = ""
                pass
            # Map exceptions to warning messages
            message, leave = {
                IOError                              : (result.bozo_exception, True),
                feedparser.zlib.error                : ("broken compression", False),
                AttributeError                       : (result.bozo_exception, True)
            }.get(exception,(msg,False))
            if message:
                log.warn("%s: %s" % (netloc, message))
            if leave: 
                self.after_fetch(feed, status = status, error = True)
                return
        
        
        if 'content-type' in headers and 'xml' not in headers['content-type']:
            log.warn("%s - content-type %s, proceeding" % (netloc, headers['content-type']))
        
        ttl = result.feed.get('ttl',None)
        etag = response.get('etag',None)
        last_modified = response.get('modified_parsed',None)
        last_modified = result.feed.get('modified_parsed',None)
        
        if status in [301,308]:
            feed.url = response['url']
        feed.ttl = ttl
        feed.etag = etag
        feed.last_modified = time.mktime(last_modified) if last_modified else None
        self.after_fetch(feed, status = status)
        feed.last_status = status

        result.entries.reverse()
        log.debug("%s - %d entries parsed" % (netloc,len(result.entries)))
        
        entries = []
        
        now = time.time()
        for entry in result.entries:
            db.close()
            when = get_entry_timestamp(entry)
            # skip ancient feed items
            if (now - when) < settings.fetcher.max_history:
                continue

            guid = get_entry_id(entry)
            try:
                item = Item.get(guid = guid)
                # if item is already in database with same timestamp, then skip it
                # TODO: handle item content updates - potentially very expensive, we'll see later on
                continue
            except Item.DoesNotExist:
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
                            'author' : get_entry_author(entry,result.feed),
                            'html'   : content,
                            'url'    : url,
                            'tags'   : get_entry_tags(entry),
                            'when'   : when,
                            'hrefs'  : hrefs})
        
        log.debug("%s - %d entries in %fs" % (netloc, len(entries),time.time()-now))
        now = time.time()
        
        records = 0
        for entry in entries:
            db.close()
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
