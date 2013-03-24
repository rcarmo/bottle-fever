#!/bin/env python
import os, sys, logging

log = logging.getLogger()

from models import User, Group, Subscription, db
from config import settings
from decorators import cached_method

class UserController:

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
    def get_group(self, title):
        db.connect()
        try:
            g = Group.get(Group.title == title)
        except Group.DoesNotExist:
            g = Group.create(title = title)
        db.close()
        return g
  
        
    def get_subscriptions_for(self, user):
        result = [s for s in Subscriptions.select(user = user)]
        db.close()
        return result
             
    def add_feed_to_group(self, user, feed, group):
        s = Subscription.create(user = user, feed = feed, group = group)
        db.close()
        return s