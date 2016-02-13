from random import randint
from jinja2 import Undefined
import logging

logger = logging.getLogger('secretary')


def list_id(list_node=None):
    return 'list%d' % (randint(100000000000000000,900000000000000000))


def pad_string(value, length=5):
    value = str(value)
    return value.zfill(length)


class UndefinedSilently(Undefined):
    # Silently undefined,
    # see http://stackoverflow.com/questions/6182498
    def silently_undefined(*args, **kwargs):
        return ''

    return_new = lambda *args, **kwargs: UndefinedSilently()

    __unicode__ = silently_undefined
    __str__ = silently_undefined
    __call__ = return_new
    __getattr__ = return_new
