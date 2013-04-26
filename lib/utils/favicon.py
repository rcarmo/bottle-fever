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
from utils import tb
from utils.urlkit import fetch, data_uri
from bs4 import BeautifulSoup

_default = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAxlBMVEUAAABOWZ5BTZhCTZhHUpt7g7d5gbZ5grZ5grZ6grZsda9sdq9tdq9tdrBtd7Bye7JxerJye7JzfLN0fbNdaKdeaadfaahfaqhha6ldZ6dfaahfaqhjbat3gLV6grZ6grd8hLh/h7mAh7mFjLxfaahgaqlha6libKpjbapRXKBSXKBSXaFTXqFUX6KNmcKXo8idqcujrs6uuNWzvdi5wtu+x96/x97EzOHJ0eXQ1ufV2+vb4O/g5fHm6vXr7/fx9Pv8/f////8y4F8aAAAALnRSTlMACR0dI1BRUVJSiIiIiIi8vb29vdbW1tbW4uLi4uzs7Ozs7Ozx8fHx8f39/f39FstVagAAALBJREFUGBllwUFOw0AMQNFve6Yhk6RFAhZsev9rwRap6iKZtp4kRrCE9+APAZGuvGX8q3oEhtgwHUexYVP2wNByei025qdx8LaF0U1noGWTdlq2VSmlhwgjNht6jPNLcpgU5HGUSyIn1UNWkEbKKCiDBz+EIOGedKpwSOP2aBixP4Pd9hZZP653ZZkrvzzqrWIE3mfRld4/Zw9BrCv9e3hcl+pbGMTaQvb1fpnXPfjnG2UzUabhPViuAAAAAElFTkSuQmCC"

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
        log.error("Could not fetch %s: %s" % (endpoint, e))
        return None
        
    try:
        soup = BeautifulSoup(res['data'])
    except Exception, e:
        log.error("Could not parse %s: %s" % (endpoint, e))
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


def fetch_anyway(site):
    global _default
    data = None
    for handler in [google_fetcher,dumb_fetcher,html_fetcher]:
        data = handler(site)
        if data:
            return data
    return _default
