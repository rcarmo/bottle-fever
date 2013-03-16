import os, sys, logging

log = logging.getLogger()

from bottle import post, request, response, abort
import time

from controllers.shim import ShimController

c = ShimController()

@post('/fever/')
def endpoint():
    print request
    api_key = request.forms.get('api_key', None)
    if not api_key or 'api' not in request.query.keys():
        abort(403,'Not Authorized')
    # TODO: validate API key
    if len(request.query.keys()) == 1: # nothing requested
        return {'api_version':1, 'auth':1,
                'last_refreshed_on_time':int(time.time())}
    
    if 'groups' in request.GET:
        return c.get_groups()
