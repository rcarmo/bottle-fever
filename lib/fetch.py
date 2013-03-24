#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
URL helper

Created by Rui Carmo on 2005-03-19, based on original code by Mark Pilgrim.
Published under the MIT license.
"""
__version__ = "0.3"

import os, sys, logging

log = logging.getLogger()

import httplib, urlparse, urllib2, gzip, re
from StringIO import StringIO
from urllib2 import HTTPRedirectHandler, HTTPDefaultErrorHandler, HTTPError

from config import settings

# Initialize debug level upon module load
httplib.HTTPConnection.debuglevel = settings.fetcher.debug_level


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


def _open_source(source, etag=None, last_modified=None):
    """Open anything"""
    if hasattr(source, 'read'):
        return source
    if source == '-':
        return sys.stdin

    if urlparse.urlparse(source)[0][:4] == 'http':
        request = urllib2.Request(source)
        request.add_header('User-Agent', settings.fetcher.user_agent)
        if etag:
            request.add_header('If-None-Match', etag)
        if last_modified:
            request.add_header('If-Modified-Since', last_modified)
        request.add_header('Accept-encoding', 'gzip')
        opener = urllib2.build_opener(SmartRedirectHandler(), DefaultErrorHandler())
        return opener.open(request, None, settings.fetcher.timeout)
    try:
        return open(source)
    except(IOError,OSError):
        pass
    return StringIO(str(source))


def fetch(url, etag=None, last_modified=None):
    """Fetch a URL and return the contents"""
    result = {}
    f = _open_source(url, etag, last_modified)
    result['data'] = f.read()
    if hasattr(f, 'headers'):
        result.update({k.lower(): f.headers.get(k) for k in f.headers})
        if f.headers.get('content-encoding', '') == 'gzip':
          result['data'] = gzip.GzipFile(fileobj=StringIO(result['data'])).read()
    if hasattr(f, 'url'):
        result['url'] = f.url
        result['status'] = 200
    if hasattr(f, 'status'):
        result['status'] = f.status
    f.close()
    return result
