import os, sys, logging

log = logging.getLogger()

from config import settings
from whoosh.fields import Schema, TEXT, ID, DATETIME, KEYWORD
from whoosh.index import create_in

item_schema = Schema(
    guid = ID(stored=True, unique=True),
    title = TEXT(stored=True),
    text = TEXT(stored=True),
    when = DATETIME(stored=True),
    tags = KEYWORD(stored=True)
)

def setup_index():
    if not os.path.exists(settings.index):
        os.makedirs(settings.index)
        ix = create_in(settings.index, item_schema)       
