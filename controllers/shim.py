#!/bin/env python
import os, sys, logging

log = logging.getLogger()

class ShimController:

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_groups(self):
        return {
            'groups': [{'id': 1, 'title': 'Test Group 1'}, {'id': 2, 'title': 'Test Group 2'}],
            'feeds_groups': [
                {'group_id': 1, 'feed_ids':'1,2'},
                {'group_id': 2, 'feed_ids':'3'}
            ]
        }
