import os, sys, logging

log = logging.getLogger()

from peewee import *

db = SqliteDatabase(':memory:')
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
    title = CharField()


class Feed(CustomModel):
    """RSS Feed"""
    favicon_id           = ForeignKeyField(Favicon)
    title                = CharField()
    url                  = CharField()
    site_url             = CharField()
    last_updated_on_time = IntegerField() # epoch

    class Meta:
        indexes = (
            (('last_updated_on_time',), False),
        )
        order_by = ('-last_updated_on_time',)


class Item(CustomModel):
    """Individual feed items"""
    guid    = CharField()
    feed_id = ForeignKeyField(Feed)
    title   = CharField()
    author  = CharField()
    html    = TextField()
    url     = CharField()
    created_on_time = IntegerField() # epoch

    class Meta:
        indexes = (
            (('feed_id',), False),
            (('created_on_time',), False),
            (('guid',), True),
            (('url',), True),
        )
        order_by = ('-created_on_time',)


class Saved(CustomModel):
    """Many-to-many relationship between Users and items"""
    user_id = ForeignKeyField(User)
    item_id = ForeignKeyField(Item)

    class Meta:
        indexes = (
            (('user_id',), False),
            (('item_id',), False),
        )

class Read(Saved):
    """Many-to-many relationship between Users and items"""
    pass
