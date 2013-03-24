#!/bin/env python
import os, sys, logging

log = logging.getLogger()

from models import User, Group, Subscription, db
from config import settings
from decorators import cached_method

class UserController:

    def __init__(self):
        pass

    def get_users(self):
        return User.select()
        

    @cached_method
    def get_user(self, username):
        return User.get(User.username == username)


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
        for s in Subscriptions.select(user = user):
            print s
             
    def add_feed_to_group(self, user, feed, group):
        db.connect()
        s = Subscription.create(user = user, feed = feed, group = group)
        db.close()
        return s