from padstring import PadStringFilter
from image import ImageFilter
from markdown import MarkdownFilter

__REGISTERED_FILTERS__ = {
    'pad': PadStringFilter,
    'image': ImageFilter,
    'markdown': MarkdownFilter,
}


def register_filter(filter_name):
    '''A decorator to register a Secretary filter.

    The filter can be a python function that takes and returns a value.
    A filter can also be a class whose inherits from SecretaryFilterInterface.

    Args:
        filter_name: Name of the filter to register.

    Example:
        from secretary.filters import register_filter

        @register_filter('square')
        def square_number(number):
            return number * number
    '''
    def _add_filter(filter_implementation):
        __REGISTERED_FILTERS__[filter_name] = filter_implementation

    return _add_filter


class RendererFilterInterface(object):
    '''
    Provies an interface for registering filters in Renderer's environment.
    '''
    filters = {}
    on_job_starts_callbacks = []
    on_job_ends_callbacks = []
    before_xml_render_callbacks = []
    after_xml_render_callbacks = []

    def __init__(self, *args, **kwargs):
        super(RendererFilterInterface, self).__init__(*args, **kwargs)

        # Register filters previously added to __REGISTERED_FILTERS__
        map(lambda (f, i): self.register_filter(f, i),
            __REGISTERED_FILTERS__.items())

    def register_filter(self, filtername, filter_imp):
        '''Registers a secretary filter.'''
        implementation = filter_imp
        if hasattr(filter_imp, 'render') and callable(filter_imp.render):
            filter_instance = filter_imp(self)
            self.filters[filtername] = filter_instance
            implementation = filter_instance.render

        self.environment.filters[filtername] = implementation

    def register_for_job_start(self, callback):
        self.on_job_starts_callbacks.append(callback)

    def register_for_job_end(self, callback):
        self.on_job_ends_callbacks.append(callback)

    def register_before_xml_render(self, callback):
        self.before_xml_render_callbacks.append(callback)

    def register_after_xml_render(self, callback):
        self.after_xml_render_callbacks.append(callback)

    def notify_job_start(self, job):
        for callback in self.on_job_starts_callbacks:
            callback(self, job)

    def notify_job_end(self, job):
        for callback in self.on_job_ends_callbacks:
            callback(self, job)

    def notify_xml_render_start(self, job, xml):
        for callback in self.before_xml_render_callbacks:
            callback(self, job, xml)

    def notify_xml_render_end(self, job, xml):
        for callback in self.after_xml_render_callbacks:
            callback(self, job, xml)
