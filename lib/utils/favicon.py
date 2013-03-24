#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Favicon retrieval

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""
import os, sys, logging

log = logging.getLogger()

import urllib2, urlparse, base64
from config import settings
from utils import data_uri
from fetch import fetch
from bs4 import BeautifulSoup


def google_fetcher(site):
    """Fetch the favicon via Google services"""
    endpoint = "http://www.google.com/s2/favicons?domain=%s" % urlparse.urlparse(site).hostname
    try:
        res = fetch(endpoint)
    except Exception, e:
        log.error("could not fetch %s: %s" % (endpoint, e))
        return None
    return data_uri(res['content-type'], res['data'])

    
def dumb_fetcher(site):
    """Fetch the favicon the dumb way"""
    endpoint = "http://%s/favicon.ico" % urlparse.urlparse(site).hostname
    try:
        res = fetch(endpoint)
    except Exception, e:
        log.error("could not fetch %s: %s" % (endpoint, e))
        return None
    return data_uri(res['content-type'], res['data'])
   
    
def html_fetcher(site):
    """Fetch the favicon the hard way"""
    endpoint = "http://%s" % urlparse.urlparse(site).hostname
    try:
        res = fetch(endpoint)
    except Exception, e:
        log.error("could not fetch %s: %s" % (endpoint, e))
        return None
        
    try:
        soup = BeautifulSoup(res['data'])
    except Exception, e:
        log.error("could not parse %s: %s" % (endpoint, e))
        return None

    link = soup.find("link", rel="shortcut icon")
    if not link:
        return None        
    url = link['href']
    try:
        res = fetch(url)
    except Exception, e:
        log.error("could not fetch %s: %s" % (endpoint, e))
        return None
    return data_uri(res['content-type'], res['data'])
    
