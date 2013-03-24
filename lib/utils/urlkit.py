#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2013, Rui Carmo
Description: Utility functions for retrieving CPU statistics
License: MIT (see LICENSE.md for details)
"""

import os, sys, time, logging

import base64
from xml.dom.minidom import parseString
from urllib import urlencode
from urllib2 import urlopen

log = logging.getLogger()

_cache = {}

def shorten(url):
    """Minimalist URL shortener using SAPO services"""
    if url not in _cache:
        u = '?'.join(('http://services.sapo.pt/PunyURL/GetCompressedURLByURL', urlencode({'url':url})))
        try:
            x = parseString(urlopen(u).read())
            _cache[url] = x.getElementsByTagName('ascii')[0].firstChild.data
        except:
            _cache[url] = url
    return _cache[url]


def data_uri(content_type, data):
    """Return data as a data: URI scheme"""
    return "data:%s;base64,%s" % (content_type, base64.urlsafe_b64encode(data))