#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Index Controller

Created by: Rui Carmo
License: MIT (see LICENSE for details)
"""

import os, sys, logging
import re, time, datetime
import socket, hashlib, urllib, urllib2, urlparse

log = logging.getLogger()

from models import Item
from bs4 import BeautifulSoup
from whoosh.index import open_dir
from whoosh.writing import BufferedWriter

class IndexController:

    def __init__(self, settings):
        feedparser.USER_AGENT = settings.fetcher.user_agent
        self.settings = settings
        self.index = open_dir(settings.index)
        self.writer = BufferedWriter(self.index, period=10, limit=20)


    def __del__(self):
        self.writer.close()


    def add_item(self, guid):
        try:
            item = Item.get(guid = guid)
        except Item.DoesNotExist:
            return False


        if len(item.html):
            soup = BeautifulSoup(item.html, self.settings.fetcher.parser)
            plaintext = ''.join(soup.find_all(text=True))
            writer.add_document(
                id    = item.id,
                guid  = unicode(item.guid),
                title = item.title,
                text  = plaintext,
                when  = datetime.datetime.utcfromtimestamp(item.when)
            )
            writer.close()
            return True
        return False
