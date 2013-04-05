#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2013, Rui Carmo
Description: Utility functions for retrieving CPU statistics
License: MIT (see LICENSE.md for details)
"""

import os, sys, logging

log = logging.getLogger()

import re, time, gzip, base64
import socket, urllib, urllib2, httplib, urlparse
from StringIO import StringIO
from xml.dom.minidom import parseString
from urllib2 import HTTPRedirectHandler, HTTPDefaultErrorHandler, HTTPError

from utils import tb
from config import settings
from decorators import memoize

# Initialize debug level upon module load
httplib.HTTPConnection.debuglevel = settings.fetcher.debug_level

@memoize
def shorten(url):
    """Minimalist URL shortener using SAPO services"""
    u = '?'.join(('http://services.sapo.pt/PunyURL/GetCompressedURLByURL', urllib.urlencode({'url':url})))
    try:
        x = parseString(fetch(u)['data'])
        return x.getElementsByTagName('ascii')[0].firstChild.data
    except:
        return url
        

@memoize
def agnostic_shortener(url):
    """A more flexible URL shortener"""
    
    services = {
        'tinyurl.com':'/api-create.php?url=',
        'is.gd'      :'/api.php?longurl=',
        #'api.bit.ly':"http://api.bit.ly/shorten?version=2.0.1&%s&format=text&longUrl=" % BITLY_AUTH,
        'api.tr.im'  :'/api/trim_simple?url='
    }
  
    for shortener in self.services.keys():
        try:
            res = fetch(self.services[shortener] + urllib.quote(url))
            shorturl = res['data'].strip()
            if ("Error" not in shorturl) and ("http://" + urlparse.urlparse(shortener)[1] in shorturl):
                return shorturl
            else:
                continue
        except:
            log.warn("%s: %s" % (tb(),url))
            pass
    return url


def expand(url, remove_junk = True, timeout = None):
    """Resolve short URLs"""
    url = unicode(url)
    result = url

    #log.debug(u"%s -> ?" % url)
    
    (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)
    
    if scheme not in ['http','https']:
        return result
    
    if netloc in ['plus.google.com','twitter.com','ads.pheedo.com']:
        return result
        
    res = {}
    try:
        res = fetch(url, head = True, timeout=timeout)
    except: 
        #log.debug(u"%s: %s" % (tb(),url))
        pass
    
    if 'url' in res:
        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(res['url'])
        if scheme not in ['http','https']:
            return result
        else: 
            result = res['url']
    
    if remove_junk:
        result = scrub_query(result)
    #log.debug(u"%s -> %s" % (url,result))
    return result    


def scrub_query(url):
    """Clean query arguments"""
    
    scrub = ["utm_source","utm_campaign","utm_medium","piwik_campaign","piwik_kwd"]
     
    url = urlparse.urldefrag(url)[0]
    base, sep, query = url.partition('?')
    seen = set()
    result = []
    for field in query.split('&'):
        name, sep, value = field.partition('=')
        if name in seen:
            continue
        elif name in scrub:
            continue
        else:
            result.append(field)
            seen.add(name)
    result = '?'.join([base, sep.join(result)]) if result else base
    # strip dangling '?'
    if result[-1:] == '?':
        result = result[:-1]
    return result


def data_uri(content_type, data):
    """Return data as a data: URI scheme"""
    return "data:%s;base64,%s" % (content_type, base64.urlsafe_b64encode(data))
    
   
class SmartRedirectHandler(HTTPRedirectHandler):

    def http_error_301(self, req, fp, code, msg, headers):
        result = HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
        result.status = code
        return result 

    def http_error_302(self, req, fp, code, msg, headers):
        result = HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        result.status = code
        return result 


class DefaultErrorHandler(HTTPDefaultErrorHandler):

    def http_error_default(self, req, fp, code, msg, headers):
        result = HTTPError(req.get_full_url(), code, msg, headers, fp) 
        result.status = code
        return result


def _open_source(source, head, etag=None, last_modified=None, timeout=None):
    """Open anything"""
    if hasattr(source, 'read'):
        return source
    if source == '-':
        return sys.stdin

    if urlparse.urlparse(source)[0][:4] == 'http':
        request = urllib2.Request(source)
        if head:
            request.get_method = lambda: 'HEAD'
        request.add_header('User-Agent', settings.fetcher.user_agent)
        if etag:
            request.add_header('If-None-Match', etag)
        if last_modified:
            request.add_header('If-Modified-Since', last_modified)
        request.add_header('Accept-encoding', 'gzip')
        opener = urllib2.build_opener(SmartRedirectHandler(), DefaultErrorHandler())
        return opener.open(request, None, timeout)
    try:
        return open(source)
    except(IOError,OSError):
        pass
    return StringIO(str(source))


def fetch(url, etag=None, last_modified=None, head = False, timeout = None):
    """Fetch a URL and return the contents"""

    result = {}
    f = _open_source(url, head, etag, last_modified, timeout)
    result['data'] = f.read()
    if hasattr(f, 'headers'):
        result.update({k.lower(): f.headers.get(k) for k in f.headers})
        if f.headers.get('content-encoding', '') == 'gzip':
            result['data'] = gzip.GzipFile(fileobj=StringIO(result['data'])).read()
    if hasattr(f.headers, 'last-modified'):
        try:
            result['modified_parsed'] = datetime.strptime(f.headers['last-modified'], "%a, %d %b %Y %H:%M:%S %Z")
        except Exception, e:
            log.debug("Could not parse Last-Modified header '%s'" % f.headers['last-modified'])
            pass
    if hasattr(f, 'url'):
        result['url'] = unicode(f.url)
        result['status'] = 200
    if hasattr(f, 'status'):
        result['status'] = f.status
    f.close()
    return result
