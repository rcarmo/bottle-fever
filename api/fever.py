import os, sys, logging

log = logging.getLogger()

from bottle import post, request, response, abort
from utils import Struct
import time, re

from controllers.users import UserController

uc = UserController()
_digits = re.compile('[0-9]+')

# TODO: caching

@post('/fever/')
def endpoint():
    result = Struct({'api_version':1, 'auth':0})
    api_key = request.forms.get('api_key', None)
    if not api_key or 'api' not in request.query.keys():
        log.debug("<- %s" % result)
        return result

    u = uc.get_user_by_api_key(api_key)
    if not u:
        log.debug("<- %s" % result)
        return result

    result.auth = 1

    if len(request.query.keys()) == 1: # nothing requested
        result.last_refreshed_on_time = int(time.time())
        log.debug("<- %s" % result)
        return result
    
    if 'groups' in request.GET:
        result.groups = uc.get_groups_for_user(u)
        result.feeds_groups = uc.get_feed_groups_for_user(u)
        log.debug("<- %s" % result)
        return result

    if 'feeds' in request.GET:
        result.feeds = uc.get_feeds_for_user(u)
        result.feeds_groups = uc.get_feed_groups_for_user(u)
        log.debug("<- %s" % result)
        return result

    if 'unread_item_ids' in request.GET:
        unread_items = uc.get_unread_items_for_user(u)
        if len(unread_items):
            result.unread_item_ids = ','.join(map(str,unread_items))
        log.debug("<- %s" %  result)
        return result

    if 'saved_item_ids' in request.GET:
        saved_items = uc.get_saved_items_for_user(u)
        if len(saved_items):
            result.saved_item_ids = ','.join(map(str,saved_items))
        log.debug("<- %s" %  result)
        return result

    if 'items' in request.GET:
        ids = [int(i) for i in request.query.get('with_ids','').split(',') if _digits.match(i)]
        since_id = int(request.query.get('since_id',0))
        if len(ids):
            result.items = uc.get_items_for_user(u, ids)
        elif since_id:
            result.items = uc.get_items_for_user_since(u, int(since_id))
        result.total_items = uc.get_item_count_for_user(u)
        log.debug("<- %s" %  result)
        return result

    # Hot links
    if 'links' in request.GET:
        result.links = [] # stubbed out until we can index content
        log.debug("<- %s" %  result)
        return result

    # TODO: handle mark, as, id
    log.debug(request.forms.keys())

