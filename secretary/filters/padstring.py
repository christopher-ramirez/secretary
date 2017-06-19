'''
    Implements Secretary's "pad" filter.
'''

class PadStringFilter():
    '''
    pad filter implementation.
    '''
    def __init__(self, renderer):
        pass

    @staticmethod
    def render(value, length=5):
        value = str(value)
        return value.zfill(length)
