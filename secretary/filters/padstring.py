'''
    Implements Secretary's "pad" filter.
'''

from .base import SecretaryFilterInterface


class PadStringFilter(SecretaryFilterInterface):
    '''pad filter implementation.'''
    @staticmethod
    def render(value, length=5):
        value = str(value)
        return value.zfill(length)
