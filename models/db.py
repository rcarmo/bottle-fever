#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2013, Rui Carmo
Description: Database models
License: MIT (see LICENSE.md for details)
"""

import os, sys, logging, inspect

log = logging.getLogger()

from config import settings
from peewee import *

if settings.db.back_end == 'sqlite3':
    db = SqliteDatabase(settings.db.sqlite3.filename, threadlocals=True, timeout=10)
elif settings.db.back_end == 'postgres':
    db = PostgresqlDatabase(settings.db.postgres.name)
    db.connect()
else:
    print "Unknown database backend"
    sys.exit(2)


class CustomModel(Model):
    """Binds the database to all our models"""

    def fields(self, fields=None, exclude=None):
        model_class = type(self)
        data = {}

        fields = fields or {}
        exclude = exclude or {}
        curr_exclude = exclude.get(model_class, [])
        curr_fields = fields.get(model_class, self._meta.get_field_names())

        for field_name in curr_fields:
            if field_name in curr_exclude:
                continue
            field_obj = model_class._meta.fields[field_name]
            field_data = self._data.get(field_name)
            if isinstance(field_obj, ForeignKeyField) and field_data and field_obj.rel_model in fields:
                rel_obj = getattr(self, field_name)
                data[field_name] = rel_obj.fields(fields, exclude)
            else:
                data[field_name] = field_data
        return data

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
    

class Feed(CustomModel):
    """RSS Feed"""
    enabled              = BooleanField(default=True)
    favicon              = ForeignKeyField(Favicon,default=1)
    title                = CharField(default='Untitled')
    url                  = CharField()
    site_url             = CharField()
    ttl                  = IntegerField(null=True,default=3600) # seconds
    filters              = CharField(null=True)
    etag                 = CharField(null=True)
    last_modified        = IntegerField(null=True) # epoch
    last_checked         = IntegerField(default=0) # epoch
    last_status          = IntegerField(null=True) # last HTTP code
    last_content         = BlobField(null=True)    # unparsed feed content
    error_count          = IntegerField(default=0)
    parsed_with          = IntegerField(default=0) # 0 for unparsed, 1 for speedparser, 2 for feedparser

    class Meta:
        indexes = (
            (('url',), True),
            (('last_modified',), False),
            (('last_checked',), False),
        )
        order_by = ('-last_modified',)


class Item(CustomModel):
    """Individual feed items"""
    guid    = CharField()
    feed    = ForeignKeyField(Feed,related_name='items')
    title   = CharField()
    author  = CharField(null=True)
    html    = TextField(null=True)
    url     = CharField()
    tags    = CharField(null=True)
    when    = IntegerField() # epoch

    class Meta:
        indexes = (
            (('when',), False),
            (('guid',), False),
            (('url',), False),
        )
        order_by = ('-when',)


class Saved(CustomModel):
    """Many-to-many relationship between Users and items"""
    user = ForeignKeyField(User)
    item = ForeignKeyField(Item)
    when = IntegerField() # epoch


class Read(Saved):
    """Many-to-many relationship between Users and items"""
    pass
    
    
class Link(CustomModel):
    url          = CharField() 
    expanded_url = CharField() 
    when         = IntegerField() # epoch

    class Meta:
        indexes = (
            (('url',), True),
            (('expanded_url',), False),
            (('when',), False),
        )
        order_by = ('url',)


class Reference(CustomModel):
    """Many-to-many relationship between items and links"""
    item = ForeignKeyField(Item)
    link = ForeignKeyField(Link)


class Subscription(CustomModel):
    """A user's feed subscriptions"""
    user  = ForeignKeyField(User)
    group = ForeignKeyField(Group)
    feed  = ForeignKeyField(Feed)


def setup(skip_if_existing = True):
    """Create tables for all models"""
    models = [User, Favicon, Feed, Item, Group, Link, Read, Saved, Subscription, Reference]

    for item in models:
        item.create_table(skip_if_existing)
    try:
        import hashlib
        User.create(username='default',api_key=hashlib.md5('default:default').hexdigest())
    except:
        pass
    try:
        import utils.favicon
        Favicon.create(id=0,data=utils.favicon._default)
    except:
        pass
    # set Write Ahead Log mode for SQLite
    if settings.db.back_end == 'sqlite3':
        db.execute_sql('PRAGMA journal_mode=WAL')

