#!/bin/env python
import os, sys, logging

log = logging.getLogger()

from models import User, Group, Subscription, Feed, Item, Read, Saved, Favicon, db
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
             

    def get_items_for_user_since(self, user, since_id, bound = 50):
        q = Item.select().join(Feed).join(Subscription).join(User).where((User.id == user.id) & (Item.id > since_id)).order_by(Item.id).distinct().limit(bound).naive()
        r = Item.select().join(Read).join(User).where((User.id == user.id) & (Item.id > since_id)).order_by(Item.id).distinct().naive()
        s = Item.select().join(Saved).join(User).where((User.id == user.id) & (Item.id > since_id)).order_by(Item.id).distinct().naive()
        read = [i.id for i in r]
        saved = [i.id for i in s]
        result = []
        for i in q:
            result.append({
                'id': i.id,
                'feed_id': i.feed.id,
                'title': i.title,
                'author': i.author,
                'html': i.html,
                'url': i.html,
                'is_saved': 1 if i.id in saved else 0,
                'is_read': 1 if i.id in read else 0,
                'created_on_time': i.when
            })
        return result


    def get_items_for_user(self, user, ids):
        q = Item.select().join(Feed).join(Subscription).join(User).where((User.id == user.id) & (Item.id << ids)).order_by(Item.id).distinct().naive()
        r = Item.select().join(Read).join(User).where((User.id == user.id) & (Item.id << ids)).order_by(Item.id).distinct().naive()
        s = Item.select().join(Saved).join(User).where((User.id == user.id) & (Item.id << ids)).order_by(Item.id).distinct().naive()
        read = [i.id for i in r]
        saved = [i.id for i in s]
        result = []
        for i in q:
            result.append({
                'id': i.id,
                'feed_id': i.feed.id,
                'title': i.title,
                'author': i.author,
                'html': i.html,
                'url': i.html,
                'is_saved': 1 if i.id in saved else 0,
                'is_read': 1 if i.id in read else 0,
                'created_on_time': i.when
            })
        return result


    @cached_method
    def get_item_count_for_user(self, user):
        q = Item.select().join(Feed).join(Subscription).join(User).where((User.id == user.id)).distinct().count()
        return q


    @cached_method
    def get_unread_items_for_user(self, user):
        q = Item.select(Item.id).join(Feed).join(Subscription).join(User).where(
            (User.id == user.id), 
            ~(Item.id << Read.select(Read.item).where(User.id == user.id))).order_by(Item.id).distinct().naive()
        return [r.id for r in q]
         

    @cached_method
    def get_saved_items_for_user(self, user):
        q = Item.select(Item.id).join(Feed).join(Subscription).join(User).where(
            (User.id == user.id), 
            (Item.id << Saved.select(Saved.item).where(User.id == user.id))).order_by(Item.id).distinct().naive()
        return [r.id for r in q]


    def add_feed_to_group(self, user, feed, group):
        s = Subscription.create(user = user, feed = feed, group = group)
        db.close()
        return s