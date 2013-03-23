#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2013, Rui Carmo
Description: Database models
License: MIT (see LICENSE.md for details)
"""

import os, sys, logging, inspect

log = logging.getLogger()

import config
from peewee import *

db = SqliteDatabase(config.settings.db,threadlocals=True)
db.connect()


class CustomModel(Model):
    """Binds the database to all our models"""
    # remember that Peewee models have an implicit integer id as primary key
    class Meta:
        database = db


class User(CustomModel):
    """Users - need at least one to store the api_key"""
    username = CharField(unique=True)
    api_key = CharField(unique=True)


class Favicon(CustomModel):
    """Feed favicons, stored as data URIs"""
    data = CharField()


class Group(CustomModel):
    """Feed group/folder"""
    title = CharField(default='Default')
    

class Filter(CustomModel):
    """Feed filters"""
    title = CharField()
    

class Feed(CustomModel):
    """RSS Feed"""
    enabled              = BooleanField(default=True)
    favicon              = ForeignKeyField(Favicon,default=0)
    title                = CharField(default='Untitled')
    url                  = CharField()
    site_url             = CharField()
    ttl                  = IntegerField(default=3600) # seconds
    apply_filter         = ForeignKeyField(Filter,default=0)
    last_updated_on_time = IntegerField(default=0) # epoch

    class Meta:
        indexes = (
            (('url',), True),
            (('last_updated_on_time',), False),
        )
        order_by = ('-last_updated_on_time',)


class Item(CustomModel):
    """Individual feed items"""
    guid    = CharField()
    feed    = ForeignKeyField(Feed)
    title   = CharField()
    author  = CharField()
    html    = TextField()
    url     = CharField()
    created_on_time = IntegerField() # epoch

    class Meta:
        indexes = (
            (('created_on_time',), False),
            (('guid',), True),
            (('url',), True),
        )
        order_by = ('-created_on_time',)


class Saved(CustomModel):
    """Many-to-many relationship between Users and items"""
    user = ForeignKeyField(User)
    item = ForeignKeyField(Item)


class Read(Saved):
    """Many-to-many relationship between Users and items"""
    pass


class Subscription(CustomModel):
    """A user's feed subscriptions"""
    user  = ForeignKeyField(User)
    group = ForeignKeyField(Group)
    feed  = ForeignKeyField(Feed)


def setup(skip_if_existing = True):
    """Create tables for all models"""
    for item in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        print item
        # make sure we only handle classes defined locally, not imports
        if item[1].__module__ == __name__:
            item[1].create_table(skip_if_existing)
    try:
        User.create(username='default',api_key='default')
    except:
        pass
