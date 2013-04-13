#!/bin/env python
import os, sys, logging

log = logging.getLogger()

from models import User, Group, Subscription, Feed, Item, Read, Favicon, db
from config import settings
from decorators import cached_method
from collections import defaultdict

class UserController:

    # TODO: move mostly feed-centric methods to the feeds controller

    @cached_method
    def get_users(self):
        result = [u for u in User.select()]
        db.close()
        return result


    @cached_method
    def get_user(self, username):
        result = User.get(User.username == username)
        db.close()
        return result


    @cached_method
    def get_user_by_api_key(self, api_key):
        result = User.get(User.api_key == api_key)
        db.close()
        return result


    @cached_method
    def get_group(self, title):
        db.connect()
        try:
            g = Group.get(Group.title == title)
        except Group.DoesNotExist:
            g = Group.create(title = title)
        db.close()
        return g
  

    @cached_method
    def get_feeds_for_user(self, user):
        q = Feed.select(Feed).join(Subscription).join(User).where(User.id == user.id).distinct().naive()
        result = []
        for f in q:
            # TODO: Change the model defaults in order to clean this up
            try:
                result.append({
                    'id'                  : f.id,
                    'favicon_id'          : f.favicon.id,
                    'title'               : f.title,
                    'url'                 : f.url,
                    'site_url'            : f.site_url,
                    'is_spark'            : 0, # TODO: implement this field in the model
                    'last_updated_on_time': f.last_checked
                })
            except Favicon.DoesNotExist:
                result.append({
                    'id'                  : f.id,
                    'favicon_id'          : 0,
                    'title'               : f.title,
                    'url'                 : f.url,
                    'site_url'            : f.site_url,
                    'is_spark'            : 0, # TODO: implement this field in the model
                    'last_updated_on_time': f.last_checked
                })
        db.close()
        return result


    @cached_method
    def get_groups_for_user(self, user):
        q = Group.select(Group).join(Subscription).join(User).where(User.id == user.id).distinct().naive()
        result = [{'id':s.id,'title':s.title} for s in q]
        db.close()
        return result


    @cached_method
    def get_feed_groups_for_user(self, user):
        q = Subscription.select(Subscription).join(User).where(User.id == user.id).distinct().naive()
        groups = defaultdict(lambda: [])
        for s in q:
            groups[str(s.group.id)].append('%d' % s.feed.id)
        result = []
        for g in groups.keys():
            result.append({'group':g, 'feed_ids':','.join(groups[g])})
        return result
             

    @cached_method
    def get_unread_items_for_user(self, user):
        q = Item.select(Item.id).join(Feed).join(Subscription).join(User).where(
            (User.id == user.id), 
            ~(Item.id << Read.select(Read.item).where(User.id == user.id))).distinct().naive()
        return ','.join([str(r.id) for r in q])
         

    def add_feed_to_group(self, user, feed, group):
        s = Subscription.create(user = user, feed = feed, group = group)
        db.close()
        return s