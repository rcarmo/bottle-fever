#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2012, Rui Carmo
Description: Utility functions
License: MIT (see LICENSE.md for details)
"""

import os, sys, time, re, logging
import json, xml.dom.minidom
import subprocess, socket, urllib, urllib2, fcntl, struct
from collections import deque

log = logging.getLogger()

# Characters used for generating page/URL aliases
ALIASING_CHARS = ['','.','-','_']

# Prefixes used to identify attachments (cid is MIME-inspired)
ATTACHMENT_SCHEMAS = ['cid','attach']

# regexp for matching caching headers
MAX_AGE_REGEX = re.compile('max-age(\s*)=(\s*)(\d+)')

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
            
    def __setitem__(self, key, value):
        super(Struct, self).__setitem__(key, value)
        self.__dict__[key] = value

    def __setattr__(self, attr, value):
        self.__setitem__(attr, value)


class InMemoryHandler(logging.Handler):
    """In memory logging handler with a circular buffer"""

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


def get_config(filename):
    """Parses the configuration file."""
    try:
        config = Struct(json.load(open(filename, 'r'),object_hook=json_str))
    except Exception, e:
        print 'Error loading configuration file %s: %s' % (filename, e)
        sys.exit(2)
    return config


def path_for(name,script=__file__):
    """Build absolute paths to resources - 2013-03-03 12:13:00"""
    if 'uwsgi' in sys.argv:
        return os.path.join(os.path.abspath(os.path.join(os.path.dirname(script),'..')),name)
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


def tb():
    """Return a concise traceback summary"""
    etype, value, tb = sys.exc_info()
    return "%s: %s (%s@%s:%d)" % (etype.__name__, value, tb.tb_frame.f_code.co_name, os.path.basename(tb.tb_frame.f_code.co_filename), tb.tb_lineno)