#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility classes and functions

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, logging

log = logging.getLogger()

import inspect, functools, json, base64
from bottle import app
from decorators import memoize
from collections import deque


class Struct(dict):
    """An object that recursively builds itself from a dict and allows easy access to attributes"""

    def __init__(self, obj):
        dict.__init__(self, obj)
        for k, v in obj.iteritems():
            if isinstance(v, dict):
                self.__dict__[k] = Struct(v)
            else:
                self.__dict__[k] = v

    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        except KeyError:
            raise AttributeError(attr)

    def __setattr__(self, attr, value):
        self.__setitem__(attr, value)


class InMemoryHandler(logging.Handler):
    """In memory logging handler with a circular buffer - 2013-02-28 10:52:02"""

    def __init__(self, limit=8192):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Our custom argument
        self.limit = limit
        self.flush()

    def emit(self, record):
        self.records.append(self.format(record))

    def flush(self):
        self.records = deque([], self.limit)

    def dump(self):
        return self.records


def json_str(item):
    """Helper function to cast JSON unicode data to plain str"""

    if isinstance(item, dict):
        #return {json_str(key): json_str(value) for key, value in item.iteritems()}
        return dict((json_str(key), json_str(value)) for key, value in item.iteritems())
    elif isinstance(item, list):
        return [json_str(element) for element in item]
    elif isinstance(item, unicode):
        return item.encode('utf-8')
    else:
        return item


@memoize
def shorten(url):
    """Minimalist URL shortener using SAPO services"""
    u = '?'.join(('http://services.sapo.pt/PunyURL/GetCompressedURLByURL',urllib.urlencode({'url':url})))
    try:
        x = xml.dom.minidom.parseString(urllib2.urlopen(u).read())
        return x.getElementsByTagName('ascii')[0].firstChild.data
    except:
        return url


_modules = {}

def reducefn(acc, upd):
    log.debug("%s, %s" % (acc, upd))
    _modules[upd['module']].append(upd)
    

def docs():
    """
    Gather all docstrings related to routes and return them grouped by module
    """
    routes = []
    modules = {}
    for route in app().routes:
        doc = inspect.getdoc(route.callback) or inspect.getcomments(route.callback)
        if not doc:
            doc = ''
        module = inspect.getmodule(route.callback).__name__
        item = {
            'method': route.method,
            'route': route.rule,
            'function': route.callback.__name__,
            'module': module,
            'doc': inspect.cleandoc(doc)
        }
        if not module in modules:
            modules[module] = []
        modules[module].append(item)
    return modules


def get_config(filename):
    """Parses the configuration file."""
    try:
        config = Struct(json.load(open(filename, 'r'),object_hook=json_str))
    except Exception, e:
        print 'Error loading configuration file %s: %s' % (filename, e)
        sys.exit(2)
    return config


def path_for(name):
    """Build absolute paths to resources - 2013-02-28 10:53:00"""
    if 'uwsgi' in sys.argv:
        return os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')),name)
    return os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),name))


def safe_eval(buffer):
    """Perform safe evaluation of a (very) small subset of Python functions"""
    if '%' == buffer[0]:
        try:
            return eval(buffer[1:],{"__builtins__":None},{"environ":os.environ})
        except Exception, e:
            log.error('Error %s while doing safe_eval of %s' % (e, buffer))
            return None
    return buffer
    

def data_uri(content_type, data):
    """Return data as a data: URI scheme"""
    return "data:%s;base64,%s" % (content_type, base64.urlsafe_b64encode(data))