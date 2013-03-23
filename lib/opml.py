#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple OPML parser

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, logging

log = logging.getLogger()

from xml.etree.cElementTree import iterparse
from xml.sax.saxutils import unescape
from collections import defaultdict

allowed_attribs = ['xmlUrl','htmlUrl','title','type','text']


def parse_file(filename):
    h = open(filename,'r')
    feeds = []
    group = ''
    for ev, el in iterparse(h,events=('start','end')):
        if ev == 'start':
            if el.tag == 'outline' and 'xmlUrl' not in el.attrib:
                group = el.attrib['text']
        elif ev == 'end':
            if el.tag == 'outline' and 'xmlUrl' in el.attrib:
                data = defaultdict(None)
                data.update({k: unescape(el.attrib[k]) for k in el.attrib if k in allowed_attribs})
                data['group'] = group
                feeds.append(data)
    h.close()
    return feeds