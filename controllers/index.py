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
from whoosh.writing import AsyncWriter

class IndexController:

    def __init__(self, settings):
        self.settings = settings
        self.index = open_dir(settings.index)
        self.writer = AsyncWriter(self.index)


    def __del__(self):
        pass


    def add_item(self, guid):
        try:
            item = Item.get(guid = guid)
        except Item.DoesNotExist:
            return False


        if len(item.html):
            soup = BeautifulSoup(item.html, self.settings.fetcher.parser)
            plaintext = ''.join(soup.find_all(text=True))
            self.writer.add_document(
                id    = item.id,
                guid  = unicode(item.guid),
                title = item.title,
                text  = plaintext,
                when  = datetime.datetime.utcfromtimestamp(item.when)
            )
            return True
        return False
