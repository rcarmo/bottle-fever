#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Feed Controller

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, time, re, urlparse, logging, hashlib
from models import Link
from utils import tb
from utils.urlkit import expand
from config import settings

log = logging.getLogger()

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


def get_link_references(soup):
    """Grab all the links from a post"""
    links = soup.find_all('a', href=re.compile('.+'))
    
    result = []
    for l in links:
        url = l['href']
        (schema, netloc, path, params, query, fragment) = urlparse.urlparse(url)
        if netloc and schema in ['http','https']:
            result.append(url)
    return result


def expand_links(links):
    """Try to expand a link without locking the database"""
    result = {}
    for l in links:
        (schema, netloc, path, params, query, fragment) = urlparse.urlparse(l)
        if netloc and schema in ['http','https']:
            try:
                link = Link.get(url = l)
                result[l] = link.expanded_url
            except Link.DoesNotExist:
                expanded_url = expand(l, timeout = settings.fetcher.link_timeout)
                try:
                    Link.create(url = l, expanded_url = expanded_url, when = time.time())
                except:
                    log.error(tb())
                result[l] = expanded_url
        else:
            result[l] = l
    return result
    