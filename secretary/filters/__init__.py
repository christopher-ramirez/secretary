from padstring import PadStringFilter
from image import ImageFilter
from markdown import MarkdownFilter

def register_filters(module):
    module.register_filter('pad')(PadStringFilter)
    module.register_filter('image')(ImageFilter)
    module.register_filter('markdown')(MarkdownFilter)
