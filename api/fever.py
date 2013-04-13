import os, sys, logging

log = logging.getLogger()

from bottle import post, request, response, abort
from utils import Struct
import time

from controllers.users import UserController

uc = UserController()

@post('/fever/')
def endpoint():
    result = Struct({'api_version':1, 'auth':0})
    print request
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
