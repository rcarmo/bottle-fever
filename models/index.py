import os, sys, logging

log = logging.getLogger()

from config import settings
from whoosh.fields import Schema, TEXT, ID, DATETIME, KEYWORD, NUMERIC
from whoosh.index import create_in

item_schema = Schema(
    id = NUMERIC(stored=True, unique=True),
    guid = TEXT(stored=True),
    title = TEXT(stored=True),
    text = TEXT(stored=True),
    when = DATETIME(stored=True),
    tags = KEYWORD(stored=True)
)

def setup_index():
    if not os.path.exists(settings.index):
        os.makedirs(settings.index)
        ix = create_in(settings.index, item_schema)       
