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

from models import Feed, Item, Link, Reference, Favicon, db
from peewee import fn
from utils.timekit import http_time
from utils.urlkit import expand, fetch
from utils.favicon import fetch_anyway
from utils import Struct, tb
from bs4 import BeautifulSoup
import markup.feedparser as feedparser
from whoosh.index import open_dir
from whoosh.writing import BufferedWriter
try:
    import markup.speedparser.speedparser as speedparser
except ImportError, e: # speedparser or its dependencies are not available
    log.error("Error importing speedparser: %s" % e)
    pass


from .tools import *

class FeedController:

    def __init__(self, settings):
        feedparser.USER_AGENT = settings.fetcher.user_agent
        self.settings = settings
        self.index = open_dir(settings.index)
        db.connect()


    def __del__(self):
        db.close()


    def get_items_from_feed(self, id):
        """Return all items from a given feed"""

        result = [Struct(i) for i in Item.select().where(Item.feed == id).dicts()]
        return result
    
    
    def get_feeds_with_counts(self, enabled = True):
        """Return feeds - defaults to returning enabled feeds only"""
        
        def _merge(i):
            r = i.fields()
            r.update({'item_count': i.item_count})
            return r
        
        result = [i for i in Feed.select().annotate(Item,fn.Count(Item.id).alias('item_count')).where(Feed.enabled == enabled)]
        result = map(_merge, result)
        return result

        
    def get_feeds(self, all = False):
        """Return feeds - defaults to returning enabled feeds only"""

        base = Feed.select(Feed.id, Feed.ttl, Feed.last_modified, Feed.last_checked, Feed.enabled)

        if all:
            result = (Struct(f) for f in base.dicts())
        else:
            result = (Struct(f) for f in base.where(Feed.enabled == True).dicts())
        return result
        
        
    def add_feed(self, url, site_url = None, title = None, group = None):
        """Add a feed to the database"""
        # existing feed?
        try:
            f = Feed.get(Feed.url == url)
        except Feed.DoesNotExist:
            f = Feed.create(url = url, title=title, site_url=site_url)
        except:
            log.error(tb())
        return f


    def update_feed(self, feed, status = None, error = False):
        if status:
            feed.last_status = status
        if error:
            feed.error_count += 1
        if feed.error_count > self.settings.fetcher.error_threshold:
            feed.enabled = False
            log.warn("%s - disabling %s" % (netloc, feed.url))
        feed.save()
    
    
    def fetch_feed(self, feed_id):
        feed = Feed.get(Feed.id == feed_id)

        if not feed.enabled:
            raise AttributeError('Feed is disabled')

        (schema, netloc, path, params, query, fragment) = urlparse.urlparse(feed.url)

        now = time.time()
            
        if feed.last_modified:
            modified = http_time(feed.last_modified)
        else:
            modified = None
        
        try:
            response = fetch(feed.url, 
                etag          = feed.etag, 
                last_modified = modified, 
                timeout       = self.settings.fetcher.fetch_timeout,
                user_agent    = settings.fetcher.user_agent)
            log.debug("%s - %d, %d" % (feed.url, response['status'], len(response['data'])))
        except Exception, e:
            log.error("Could not fetch %s: %s" % (feed.url, e))
            # TODO: store reason properly
            # Network connect timeout error (Unknown)
            self.update_feed(feed, status = 599, error = True)
            raise
            
        feed.last_checked = now
        status = response['status']

        if status == 304: # not modified
            log.warn("%s - not modified." % netloc)
            self.update_feed(feed, status = status)
            return False
        elif status == 410: # gone
            log.warn("%s - gone, disabling %s" % (netloc, feed.url))
            feed.enabled = False
            self.update_feed(feed, status = status)
            return False
        elif status not in [200,301,302,307,308]:
            log.warn("%s - %d, aborting" % (netloc,status))
            self.update_feed(feed, status = status, error = True)
            return False

        if 'content-type' in response.keys() and 'xml' not in response['content-type']:
            log.warn("%s - content-type %s, proceeding" % (netloc, response['content-type']))

        if status in [301,308]:
            feed.url = response['url']

        feed.last_status = status
        feed.ttl = 0
        feed.etag = response.get('etag',None)
        last_modified = response.get('modified_parsed',None)
        feed.last_modified = time.mktime(last_modified) if last_modified else None

        if not response['data']:
            return False

        if feed.last_content and (hashlib.md5(feed.last_content).digest() == hashlib.md5(response['data']).digest()):
            return False

        feed.last_content = response['data']
        feed.save()
        return True


    def parse_feed(self, feed_id):
        """Parse a feed and return a set of items"""
        feed = Feed.get(Feed.id == feed_id)

        if not feed.enabled:
            raise AttributeError('Feed is disabled')        

        if feed.error_count and feed.parsed_with == 1: # there were errors last time around, so let's try feedparser this time
            try:
                result = feedparser.parse(feed.last_content)
                feed.parsed_with = 2
            except Exception, e:
                log.error("Could not parse %s with feedparser: %s" % (feed.url, e))
                # Invalid response from upstream server
                self.update_feed(feed, status = 502, error = True)
                return
        else:
            try:
                result = speedparser.parse(feed.last_content)
                feed.parsed_with = 1
            except Exception, e:
                log.error("Could not parse %s with speedparser: %s" % (feed.url, e))
                try:
                    result = feedparser.parse(feed.last_content)
                    feed.parsed_with = 2
                except Exception, e:
                    log.error("Could not parse %s with feedparser: %s" % (feed.url, e))
                    # Invalid response from upstream server
                    self.update_feed(feed, status = 502, error = True)
                    return
        
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
                log.warn("%s: %s" % (feed.url, message))
            if leave: 
                self.update_feed(feed, status = 502, error = True)
                return
                
        feed.ttl = result.feed.get('ttl',None)
        feed.save()
        if not len(result.entries):
            return

        if not feed.last_modified:
            feed.last_modified = get_entry_timestamp(result.entries[0])
            feed.save()

        result.entries.reverse()

        log.debug("%s - %d entries parsed" % (feed.url,len(result.entries)))

        now = time.time()
        for entry in result.entries:
            when = get_entry_timestamp(entry)
            # skip ancient feed items
            if (now - when) > self.settings.fetcher.max_history:
                continue

            guid = get_entry_id(entry)
            try:
                item = Item.get(guid = guid)
                # if item is already in database with same timestamp, then skip it
                # TODO: handle item content updates - potentially very expensive, we'll see later on
                continue
            except Item.DoesNotExist:
                pass
            except Exception, e:
                log.error(tb())

            html = get_entry_content(entry)
            yield  {'guid'   : guid,
                    'feed'   : feed.id,
                    'title'  : get_entry_title(entry),
                    'author' : get_entry_author(entry,result.feed),
                    'html'   : html,
                    'url'    : entry.link,
                    'tags'   : get_entry_tags(entry),
                    'when'   : when}
    

    def parse_item(self, entry):   
        records = 0

        guid = entry['guid']
        try:
            item = Item.get(guid = guid)
        except Item.DoesNotExist:
            item = Item.create(**entry)
        records += 1

        if len(entry['html']):
            soup = BeautifulSoup(entry['html'], self.settings.fetcher.parser)
            hrefs = get_link_references(soup)
        else:
            hrefs = []
        hrefs.append(entry['url'])
        
        if not self.settings.fetcher.post_processing.expand_links:
            return guid

        links = expand_links(set(hrefs))
        # TODO: replace hrefs in content, avoiding creating the item twice
        # including item url = hrefs[entry.link]
        # ...and handling updates
        #links = list(set(links.values()))
        links = set(links.values())
        
        for link in links:
            try:
                reference = Reference.get(item = item, link = Link.get(expanded_url = link))
            except Reference.DoesNotExist:
                reference = Reference.create(item = item, link = Link.get(expanded_url = link))
                records += 1
            except:
                log.error(tb())
        return guid


    def update_favicon(self, feed_id):
        feed = Feed.get(Feed.id == feed_id)
        try:
            favicon = Favicon.get(id = feed.favicon)
        except Favicon.DoesNotExist:
            favicon = Favicon.create(data=fetch_anyway(feed.site_url))
            feed.favicon = favicon
            feed.save()
