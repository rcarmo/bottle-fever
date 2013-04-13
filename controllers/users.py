#!/bin/env python
import os, sys, logging

log = logging.getLogger()

from models import User, Group, Subscription, db
from config import settings
from decorators import cached_method
from collections import defaultdict

class UserController:

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
        log.debug(groups)
        result = []
        for g in groups.keys():
            result.append({'group':g, 'feed_ids':','.join(groups[g])})
        return result
             
    def add_feed_to_group(self, user, feed, group):
        s = Subscription.create(user = user, feed = feed, group = group)
        db.close()
        return s