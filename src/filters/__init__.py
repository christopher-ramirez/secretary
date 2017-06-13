from padstring import PadStringFilter
from image import ImageFilter

def register_filters(module):
    module.register_filter('pad')(PadStringFilter)
    module.register_filter('image')(ImageFilter)
