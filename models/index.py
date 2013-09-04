import os, sys, logging

log = logging.getLogger()

from config import settings
from whoosh.fields import Schema, TEXT, ID, DATETIME, KEYWORD, NUMERIC
from whoosh.index import create_in, exists_in

item_schema = Schema(
    id = NUMERIC(stored=True, unique=True),
    guid = TEXT(stored=True),
    title = TEXT(stored=True),
    text = TEXT(stored=True),
    when = DATETIME(stored=True),
    tags = KEYWORD(stored=True)
)

def setup(skip_if_existing=True):
    if not os.path.exists(settings.index):
        os.makedirs(settings.index)

    if exists_in(settings.index) and skip_if_existing:
    	return

    ix = create_in(settings.index, item_schema)       
